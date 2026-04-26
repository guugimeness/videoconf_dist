import zmq
import time


XSUB_PORT = 5555
XPUB_PORT = 5556
AUTH_PORT = 5557  # Nova porta para o login
SESSION_TIMEOUT = 30  # Segundos sem receber mensagem antes de derrubar o usuário


def main():
    context = zmq.Context()

    print("[BROKER] Iniciando broker ativo...")

    # Sockets
    frontend = context.socket(zmq.XSUB)
    frontend.setsockopt(zmq.RCVHWM, 100)
    frontend.bind(f"tcp://*:{XSUB_PORT}")

    backend = context.socket(zmq.XPUB)
    backend.setsockopt(zmq.SNDHWM, 100)
    backend.bind(f"tcp://*:{XPUB_PORT}")

    # Socket de Autenticação (REQ/REP)
    auth_socket = context.socket(zmq.REP)
    auth_socket.bind(f"tcp://*:{AUTH_PORT}")

    # Poller
    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(backend, zmq.POLLIN)
    poller.register(auth_socket, zmq.POLLIN)

    # Estado da sessão
    active_users = {}
    
    msg_count = 0

    try:
        while True:
            socks = dict(poller.poll(1000))
            current_time = time.time()

            # TRATAMENTO DE LOGIN
            if auth_socket in socks:
                request = auth_socket.recv_string()
                print(request)
                try:
                    # Esperado: "LOGIN|SALA_A|user1"
                    acao, sala, usuario = request.split("|")
                    if acao == "LOGIN":
                        if usuario in active_users:
                            auth_socket.send_string("ERRO: Nome já está em uso.")
                            print(f"[AUTH] Acesso negado para '{usuario}' (nome duplicado).")
                        else:
                            # Registra usuário e guarda o timestamp atual
                            active_users[usuario] = {"room": sala, "last_seen": current_time}
                            auth_socket.send_string("OK")
                            print(f"[AUTH] '{usuario}' entrou na sala '{sala}'.")
                            
                            # BÔNUS: O broker injeta uma mensagem de sistema no chat avisando que ele entrou!
                            aviso = f"{sala}:TEXTO:SISTEMA:0|O usuário '{usuario}' entrou na sala."
                            backend.send(aviso.encode('utf-8'))
                            
                except Exception as e:
                    auth_socket.send_string(f"ERRO: Formato inválido ({e})")

            # MENSAGENS DOS PUBLISHERS
            if frontend in socks:
                # Recebemos em bytes, pois pode ser áudio, vídeo ou texto
                parts = frontend.recv_multipart()

                try:
                    sender_name = None
                    
                    # Se for o formato de VÍDEO do seu colega [room, sender, msg_id, timestamp, payload]
                    if len(parts) == 5:
                        sender_name = parts[1].decode('utf-8', errors='ignore')
                    
                    # Se for o formato de TEXTO/ÁUDIO/HEARTBEAT seu ("SALA:TEXTO:NOME:ID|payload")
                    elif len(parts) == 1:
                        header_parts = parts[0].split(b"|", 1)
                        if len(header_parts) >= 1:
                            header_str = header_parts[0].decode('utf-8', errors='ignore')
                            header_pieces = header_str.split(":")
                            if len(header_pieces) >= 3:
                                sender_name = header_pieces[2]

                    # Atualiza a sessão provando que o usuário está vivo (independente da mídia enviada)
                    if sender_name and sender_name in active_users:
                        active_users[sender_name]["last_seen"] = current_time
                except Exception:
                    pass 

                # O Broker repassa a mensagem exatamente como chegou (Multiparte)
                backend.send_multipart(parts)

            # INSCRIÇÕES DOS SUBSCRIBERS
            if backend in socks:
                subscription = backend.recv()
                frontend.send(subscription)

            # CONTROLE DE PRESENÇA (TIMEOUT)
            dead_users = []
            for user, info in active_users.items():
                if current_time - info["last_seen"] > SESSION_TIMEOUT:
                    dead_users.append(user)

            # Remove os desconectados e libera o nome deles
            for user in dead_users:
                sala = active_users[user]["room"]
                print(f"[SESSÃO] '{user}' desconectado por inatividade.")
                del active_users[user]
                
                # BÔNUS: Broker avisa a sala que ele caiu
                aviso = f"{sala}:TEXTO:SISTEMA:0|O usuário '{user}' foi desconectado."
                backend.send(aviso.encode('utf-8'))

    except KeyboardInterrupt:
        print("\n[BROKER] Encerrando...")
    finally:
        frontend.close()
        backend.close()
        auth_socket.close()
        context.term()

if __name__ == "__main__":
    main()