import zmq
import threading
import sounddevice as sd
import numpy as np
import queue
import time
from collections import deque
import shared.config as cfg
from shared import broker_discovery


SAMPLE_RATE = 44100
CHUNK = 1024
CODEC = np.int16  # Compressão: float32 → int16 (reduz 50% bandwidth)
JITTER_BUFFER_SIZE = 10  # Quantos frames para buffer de jitter
HEARTBEAT_INTERVAL = 5  # segundos
HEARTBEAT_TIMEOUT = 15  # segundos
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 2  # segundos


class AudioClient:
    """Cliente de áudio robusto com reconexão, compressão e jitter buffer."""
    
    def __init__(self, user_name, room, broker_host=None, pub_port=None, sub_port=None, auth_port=None):
        self.user_name = user_name
        self.room = room
        
        # Descoberta de broker via parâmetros ou config
        if broker_host is None:
            broker_config = broker_discovery.get_broker_for_user(user_name)
            self.broker_host = broker_config['host']
            self.pub_port = broker_config['publish_port']
            self.sub_port = broker_config['subscribe_port']
        else:
            self.broker_host = broker_host
            self.pub_port = pub_port or cfg.PUBLISH_PORT
            self.sub_port = sub_port or cfg.SUBSCRIBE_PORT

        self.input_device = cfg.AUDIO_INPUT_DEVICE
        self.output_device = cfg.AUDIO_OUTPUT_DEVICE

        self.input_rate = int(sd.query_devices(self.input_device)['default_samplerate'])
        self.output_rate = int(sd.query_devices(self.output_device)['default_samplerate'])

        self.channels = cfg.AUDIO_CHANNELS
        
        # Comunicação thread-safe entre callback e socket
        self.audio_queue = queue.Queue(maxsize=100)  # Fila de áudio
        
        # Jitter buffer (deque thread-safe)
        self.jitter_buffer = deque(maxlen=JITTER_BUFFER_SIZE)
        self.jitter_lock = threading.Lock()
        
        # Sinais de controle
        self.stop_event = threading.Event()
        self.connected_event = threading.Event()
        self.last_heartbeat = time.time()
        
        # Stats
        self.sent_frames = 0
        self.received_frames = 0


    def send_audio(self):
        """Thread 1: Captura áudio e coloca na fila."""
        
        def audio_callback(indata, frames, time_info, status):
            if status:
                # print(f"[ÁUDIO] ⚠️  Status callback: {status}")
                return
            
            try:
                # Converte float32 [-1, 1] → int16 [-32768, 32767]
                audio_data = np.clip(indata * 32767, -32768, 32767).astype(CODEC)
                
                # Coloca na fila (non-blocking)
                try:
                    self.audio_queue.put_nowait(audio_data.tobytes())
                except queue.Full:
                    print("[ÁUDIO] Fila de captura cheia - frame descartado")
                    
            except Exception as e:
                print(f"[ÁUDIO] Erro no callback: {e}")
        
        # Inicia stream de captura
        try:
            with sd.InputStream(
                device=self.input_device,
                samplerate=self.input_rate,
                channels=self.channels,
                blocksize=CHUNK,
                callback=audio_callback,
                dtype='float32',
                latency='low',
            ):
                # print("[ÁUDIO] ✓ Captura iniciada")
                
                # Aguarda sinal de parada
                while not self.stop_event.is_set():
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"[ÁUDIO] Erro na captura: {e}")


    def send_audio_to_broker(self):
        """Thread 2: Envia áudio da fila para o broker com reconexão."""
        
        reconnect_count = 0
        current_broker = broker_discovery.get_broker_for_user(self.user_name)
        
        while not self.stop_event.is_set():
            try:
                # Reconexão
                context = zmq.Context()
                socket = context.socket(zmq.PUB)
                socket.setsockopt(zmq.LINGER, 0)
                
                addr = f"tcp://{current_broker['host']}:{current_broker['publish_port']}"
                socket.connect(addr)
                
                print(f"[ÁUDIO→BROKER] ✓ Conectado ao broker {current_broker['broker_id']}: {addr}")
                self.connected_event.set()
                reconnect_count = 0
                
                # Loop de envio
                while not self.stop_event.is_set():
                    try:
                        # Tira áudio da fila (timeout para permitir reconexão)
                        audio_bytes = self.audio_queue.get(timeout=1.0)
                        
                        # Formato: "SALA:AUDIO:NOME|audio_bytes"
                        topic = f"{self.room}:AUDIO:{self.user_name}|".encode()
                        socket.send(topic + audio_bytes)
                        
                        self.sent_frames += 1
                        
                    except queue.Empty:
                        continue
                    except zmq.error.ZMQError:
                        # Conexão perdida, tenta reconectar
                        break
                        
            except zmq.error.Again:
                print("[ÁUDIO→BROKER] Timeout ao enviar")
                self.connected_event.clear()
                
            except Exception as e:
                print(f"[ÁUDIO→BROKER] Erro: {e}")
                self.connected_event.clear()
                
                # Reconexão com backoff exponencial e fallback
                reconnect_count = min(reconnect_count + 1, MAX_RECONNECT_ATTEMPTS)
                delay = RECONNECT_DELAY * (2 ** (reconnect_count - 1))
                
                if reconnect_count >= MAX_RECONNECT_ATTEMPTS:
                    # Tenta outro broker
                    fallback = broker_discovery.select_fallback_broker(current_broker, self.user_name)
                    if fallback:
                        print(f"[ÁUDIO→BROKER] Broker {current_broker['broker_id']} indisponível. Tentando broker {fallback['broker_id']}...")
                        current_broker = fallback
                        reconnect_count = 0
                        delay = RECONNECT_DELAY
                    else:
                        print("[ÁUDIO→BROKER] Nenhum broker disponível")
                
                print(f"[ÁUDIO→BROKER] Reconectando em {delay}s (tentativa {reconnect_count}/{MAX_RECONNECT_ATTEMPTS})")
                time.sleep(delay)
                
            finally:
                try:
                    socket.close()
                    context.term()
                except:
                    pass


    def receive_audio(self):
        """Thread 3: Recebe áudio do broker e coloca no jitter buffer."""
        
        reconnect_count = 0
        current_broker = broker_discovery.get_broker_for_user(self.user_name)
        
        while not self.stop_event.is_set():
            try:
                context = zmq.Context()
                socket = context.socket(zmq.SUB)
                socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5s timeout
                
                addr = f"tcp://{current_broker['host']}:{current_broker['subscribe_port']}"
                socket.connect(addr)
                
                # Assina: "SALA:AUDIO:" (mas não do próprio usuário)
                topic = f"{self.room}:AUDIO:".encode()
                socket.setsockopt(zmq.SUBSCRIBE, topic)
                
                print(f"[ÁUDIO←BROKER] ✓ Conectado ao broker {current_broker['broker_id']}: {addr}")
                reconnect_count = 0
                
                # Loop de recepção
                while not self.stop_event.is_set():
                    try:
                        message = socket.recv()
                        
                        # Parse: "SALA:AUDIO:NOME|audio_bytes"
                        try:
                            header, audio_bytes = message.split(b"|", 1)
                            parts = header.decode().split(":")
                            sender = parts[2]
                            
                            # Ignora próprio áudio
                            if sender == self.user_name:
                                continue
                            
                            # Coloca no jitter buffer
                            with self.jitter_lock:
                                self.jitter_buffer.append(audio_bytes)
                                
                            self.received_frames += 1
                            
                        except (ValueError, IndexError, UnicodeDecodeError) as e:
                            print(f"[ÁUDIO←BROKER] Pacote malformado: {e}")
                            continue
                    
                    except zmq.error.Again:
                        pass
                        # print("[ÁUDIO←BROKER] Timeout na recepção")
                    
                    except zmq.error.ZMQError:
                        # Conexão perdida
                        break
                        
            except Exception as e:
                print(f"[ÁUDIO←BROKER] Erro: {e}")
                
                # Reconexão com backoff exponencial e fallback
                reconnect_count = min(reconnect_count + 1, MAX_RECONNECT_ATTEMPTS)
                delay = RECONNECT_DELAY * (2 ** (reconnect_count - 1))
                
                if reconnect_count >= MAX_RECONNECT_ATTEMPTS:
                    # Tenta outro broker
                    fallback = broker_discovery.select_fallback_broker(current_broker, self.user_name)
                    if fallback:
                        print(f"[ÁUDIO←BROKER] Broker {current_broker['broker_id']} indisponível. Tentando broker {fallback['broker_id']}...")
                        current_broker = fallback
                        reconnect_count = 0
                        delay = RECONNECT_DELAY
                    else:
                        print("[ÁUDIO←BROKER] Nenhum broker disponível")
                
                print(f"[ÁUDIO←BROKER] Reconectando em {delay}s")
                time.sleep(delay)
                
            finally:
                try:
                    socket.close()
                    context.term()
                except:
                    pass


    def playback_audio(self):
        """Thread 4: Reproduz áudio do jitter buffer."""
        
        try:
            with sd.OutputStream(
                device=self.output_device,
                samplerate=self.output_rate,
                channels=self.channels,
                blocksize=CHUNK
            ) as stream:
                # print("[ÁUDIO-PLAYBACK] ✓ Playback iniciado")
                
                while not self.stop_event.is_set():
                    try:
                        # Tira do jitter buffer
                        with self.jitter_lock:
                            if len(self.jitter_buffer) > 0:
                                audio_bytes = self.jitter_buffer.popleft()
                            else:
                                audio_bytes = None
                        
                        if audio_bytes:
                            # Reconverte int16 → float32 [-1, 1]
                            audio = np.frombuffer(audio_bytes, dtype=CODEC).astype(np.float32) / 32767.0

                            # duplica canal (mono → stereo)
                            audio = np.repeat(audio[:, np.newaxis], self.channels, axis=1)
                            
                            stream.write(audio)
                        else:
                            time.sleep(0.01)  # Pequeno delay se vazio
                            
                    except Exception as e:
                        print(f"[ÁUDIO-PLAYBACK] Erro: {e}")
                        time.sleep(0.1)
                        
        except Exception as e:
            print(f"[ÁUDIO-PLAYBACK] Erro ao iniciar: {e}")


    def heartbeat_monitor(self):
        """Thread 5: Monitora saúde da conexão com heartbeat."""
        
        while not self.stop_event.is_set():
            try:
                # Verifica se há frames sendo recebidos
                last_count = self.received_frames
                time.sleep(HEARTBEAT_INTERVAL)
                
                # if self.received_frames == last_count and self.received_frames > 0:
                #     print("[HEARTBEAT] Nenhum áudio recebido nos últimos segundos")
                    
            except Exception as e:
                print(f"[HEARTBEAT] Erro: {e}")


    def print_stats(self):
        """Imprime estatísticas a cada 10s."""
        
        while not self.stop_event.is_set():
            try:
                time.sleep(10)
                qsize = self.audio_queue.qsize()
                buffer_size = len(self.jitter_buffer)
                
                # print(f"\n[STATS] 📊 Enviados: {self.sent_frames} | "
                #       f"Recebidos: {self.received_frames} | "
                #       f"Fila: {qsize} | "
                #       f"Buffer: {buffer_size}\n")
                      
            except Exception as e:
                print(f"[STATS] Erro: {e}")


    def start(self):
        """Inicia todas as threads."""
        
        threads = [
            ("Captura", self.send_audio),
            ("Envio→Broker", self.send_audio_to_broker),
            ("Recepção←Broker", self.receive_audio),
            ("Playback", self.playback_audio),
            ("Heartbeat", self.heartbeat_monitor),
            ("Stats", self.print_stats),
        ]
        
        for name, target in threads:
            t = threading.Thread(target=target, daemon=True, name=name)
            t.start()
        
        # print(f"[ÁUDIO] ✓ {self.user_name} conectado na sala {self.room}\n")


    def stop(self):
        """Para todas as threads."""
        self.stop_event.set()
        time.sleep(1)
        # print("\n[ÁUDIO] ✓ Desconectado")


def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python client_audio.py <NOME> <SALA>")
        print("Exemplo: python client_audio.py user1 SALA_A")
        return
    
    user_name = sys.argv[1]
    room = sys.argv[2]
    
    client = AudioClient(user_name, room)
    client.start()
    
    try:
        # Keep-alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[ÁUDIO] Encerrando...")
        client.stop()

def get_default_devices():
    input_device = sd.default.device[0]
    output_device = sd.default.device[1]
    
    # print(f"[ÁUDIO] Input device: {input_device}")
    # print(f"[ÁUDIO] Output device: {output_device}")
    
    return input_device, output_device

if __name__ == "__main__":
    main()