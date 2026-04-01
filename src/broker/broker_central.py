import zmq
import time


def main():
    # Broker Central: 
    # Recebe mensagens dos publishers (clientes enviando mídia) e 
    # distribui para os subscribers (clientes recebendo mídia).
    
    context = zmq.Context()
    print("[BROKER] Iniciando Broker Central...")

    # Socket onde os clientes vão publicar os dados 
    frontend = context.socket(zmq.XSUB)
    frontend.bind("tcp://*:5555")  
    print("[BROKER] Escutando publishers na porta 5555")

    # Socket onde os clientes vão assinar para receber dados
    backend = context.socket(zmq.XPUB)
    backend.bind("tcp://*:5556")  
    print("[BROKER] Distribuindo para subscribers na porta 5556")

    try:
        zmq.proxy(frontend, backend)
    except zmq.ContextTerminated:
        print("[BROKER] Contexto ZeroMQ encerrado.")
    except KeyboardInterrupt:
        print("\n[BROKER] Encerrando o Broker Central manualmente.")
    finally:
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    main()