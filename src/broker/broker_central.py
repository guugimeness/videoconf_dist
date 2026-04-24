import zmq
import time

XSUB_PORT = 5555
XPUB_PORT = 5556

def main():
    context = zmq.Context()

    print("[BROKER] Iniciando broker ativo...")

    frontend = context.socket(zmq.XSUB)
    frontend.bind(f"tcp://*:{XSUB_PORT}")

    backend = context.socket(zmq.XPUB)
    backend.bind(f"tcp://*:{XPUB_PORT}")

    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(backend, zmq.POLLIN)

    msg_count = 0
    start_time = time.time()

    try:
        while True:
            socks = dict(poller.poll(1000))

            # 📥 Mensagens dos publishers
            if frontend in socks:
                message = frontend.recv()

                msg_count += 1

                # DEBUG opcional
                if msg_count % 100 == 0:
                    print(f"[BROKER] {msg_count} mensagens processadas")

                backend.send(message)

            # 📡 Subscriptions dos subscribers
            if backend in socks:
                subscription = backend.recv()

                # Encaminha subscription para publishers
                frontend.send(subscription)

    except KeyboardInterrupt:
        print("\n[BROKER] Encerrando...")

    finally:
        frontend.close()
        backend.close()
        context.term()


if __name__ == "__main__":
    main()