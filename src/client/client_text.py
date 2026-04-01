import zmq
import threading
import sys
import shared.config as cfg


def receive_messages(context, user_name, room):
    # Thread dedicada a escutar as mensagens do broker.
    
    # Conecta no backend do Broker
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{cfg.BROKER_HOST}:{cfg.SUBSCRIBE_PORT}")
    
    # Assina apenas as mensagens de texto da sala especificada
    topic = f"{room}:TEXTO:"
    socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    
    while True:
        try:
            # Recebe a mensagem bruta
            message = socket.recv_string()
            
            # Formato esperado: "SALA:TEXTO:NOME|Mensagem"
            header, content = message.split("|", 1)
            _, _, sender = header.split(":")
            
            # Evita imprimir a própria mensagem
            if sender != user_name:
                print(f"\r[{sender}]: {content}\n> ", end="", flush=True)
                
        except zmq.ContextTerminated:
            break
        except Exception as e:
            print(f"Erro na recepção: {e}")


def main():
    if len(sys.argv) < 3:
        print("Uso: python client_texto.py <SEU_NOME> <SALA>")
        print("Exemplo: python client_texto.py Joao SALA_A")
        sys.exit(1)

    user_name = sys.argv[1]
    room = sys.argv[2]

    context = zmq.Context()

    # Inicia a thread de recepção (Subscriber)
    recv_thread = threading.Thread(target=receive_messages, args=(context, user_name, room), daemon=True)
    recv_thread.start()

    # Conecta no frontend do Broker
    socket_pub = context.socket(zmq.PUB)
    socket_pub.connect(f"tcp://{cfg.BROKER_HOST}:{cfg.PUBLISH_PORT}")

    print(f"Bem-vindo(a) {user_name} à {room}!")
    print("Digite sua mensagem e aperte Enter (Ctrl+C para sair):")
    
    try:
        while True:
            # O input bloqueia a thread principal aguardando a digitação
            text = input("> ")
            if text:
                # Monta a mensagem estruturada com o tópico
                # Exemplo: "SALA_A:TEXTO:Joao|Olá pessoal!"
                formatted_message = f"{room}:TEXTO:{user_name}|{text}"
                socket_pub.send_string(formatted_message)
                
    except KeyboardInterrupt:
        print("\nDesconectando...")
    finally:
        context.term()

if __name__ == "__main__":
    main()