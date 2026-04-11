import zmq
import time
import threading
import queue
from dataclasses import dataclass

MAX_QUEUE_PER_ROOM = 30

@dataclass
class VideoMessage:
    room: bytes
    sender: bytes
    msg_id: bytes
    timestamp: bytes
    payload: bytes

    def to_multipart(self):
        return [self.room, self.sender, self.msg_id, self.timestamp, self.payload]

    @staticmethod
    def from_multipart(parts):
        if len(parts) < 5:
            return None
        return VideoMessage(*parts[:5])


class VideoBroker:
    def __init__(self,
                 pub_port=5555,
                 sub_port=5556,
                 broker_id="broker_A"):
        self.pub_port = pub_port
        self.sub_port = sub_port
        self.broker_id = broker_id

        self.context = zmq.Context()
        self.running = False

        # clientes publicam aqui
        self.frontend = self.context.socket(zmq.XSUB)
        self.frontend.bind(f"tcp://*:{self.pub_port}")

        # clientes recebem daqui
        self.backend = self.context.socket(zmq.XPUB)
        self.backend.bind(f"tcp://*:{self.sub_port}")

        self.proxy_thread = None
        self.cluster_thread = None

        # QoS por sala
        self.room_queues = {}
        self.local_rooms = {"A", "B", "C"}

    def start(self):
        self.running = True
        print(f"[{self.broker_id}] Broker iniciado")
        print(f"[{self.broker_id}] Publishers na porta {self.pub_port}")
        print(f"[{self.broker_id}] Subscribers na porta {self.sub_port}")

        self.proxy_thread = threading.Thread(target=self.proxy_loop)
        self.cluster_thread = threading.Thread(target=self.interbroker_loop)

        self.proxy_thread.start()
        self.cluster_thread.start()

    def proxy_loop(self):
        try:
            zmq.proxy(self.frontend, self.backend)
        except zmq.ContextTerminated:
            print(f"[{self.broker_id}] Contexto encerrado")
        except Exception as e:
            print(f"[{self.broker_id}] Erro no proxy: {e}")

    def route_room_message(self, message):
        """
        Roteamento por salas + QoS no broker.
        Formato: [room, sender, msg_id, timestamp, payload]
        """
        if len(message) < 5:
            self.backend.send_multipart(message)
            return

        parsed = VideoMessage.from_multipart(message)
        if parsed is None:
            self.backend.send_multipart(message)
            return

        room_name = parsed.room.decode(errors="ignore")

        # só processa salas locais deste broker
        if room_name not in self.local_rooms:
            return

        if room_name not in self.room_queues:
            self.room_queues[room_name] = queue.Queue(maxsize=MAX_QUEUE_PER_ROOM)

        q = self.room_queues[room_name]

        # QoS: descarta backlog antigo
        if q.full():
            try:
                q.get_nowait()
            except queue.Empty:
                pass

        q.put(message)
        self.backend.send_multipart(message)

    def stop(self):
        self.running = False
        self.frontend.close()
        self.backend.close()
        self.context.term()
        print(f"[{self.broker_id}] Broker encerrado")


    # =========================
    # CLUSTER ENTRE BROKERS
    # =========================
    def connect_to_peer(self, peer_host, peer_pub_port=5555):
        """
        Conecta este broker ao canal de publicação de outro broker.
        Permite encaminhamento entre clusters.
        """
        peer_socket = self.context.socket(zmq.SUB)
        peer_socket.connect(f"tcp://{peer_host}:{peer_pub_port}")
        peer_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        if not hasattr(self, 'peer_sockets'):
            self.peer_sockets = []

        self.peer_sockets.append(peer_socket)
        print(f"[{self.broker_id}] Conectado ao peer {peer_host}:{peer_pub_port}")

    def interbroker_loop(self):
        """
        Recebe frames de outros brokers e redistribui localmente.
        Agora com prevenção básica de loops.
        """
        if not hasattr(self, 'seen_messages'):
            self.seen_messages = set()

        while self.running:
            for peer in getattr(self, 'peer_sockets', []):
                try:
                    message = peer.recv_multipart(flags=zmq.NOBLOCK)

                    # formato esperado: [room, sender, msg_id, payload]
                    if len(message) == 5:
                        room, sender, msg_id, timestamp, payload = message
                        msg_key = msg_id.decode(errors='ignore')

                        if msg_key in self.seen_messages:
                            continue

                        self.seen_messages.add(msg_key)
                        self.route_room_message(message)
                    else:
                        # compatibilidade com mensagens legadas
                        self.route_room_message(message)

                except zmq.Again:
                    pass
                except Exception as e:
                    print(f"[{self.broker_id}] Erro inter-broker: {e}")

            # evita crescimento infinito da memória
            if len(getattr(self, 'seen_messages', set())) > 5000:
                self.seen_messages.clear()

            time.sleep(0.005)


if __name__ == "__main__":
    broker = VideoBroker()

    # salas locais deste broker (exemplo A-C)
    broker.local_rooms = {"A", "B", "C"}

    # Exemplo para cluster: conectar a outro broker
    # broker.connect_to_peer("192.168.0.10", 5555)

    try:
        broker.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        broker.stop()
