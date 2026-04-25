import sys
import threading
from client.client_text import TextClient
from client.client_audio import AudioClient


def main():
    if len(sys.argv) < 3:
        print("Uso: python client_main.py <SEU_NOME> <SALA>")
        return

    user_name = sys.argv[1]
    room = sys.argv[2]

    print(f"[{user_name}] Iniciando videoconferência na sala {room}...")

    # Instancia os dois clientes
    text_client = TextClient(user_name, room)
    audio_client = AudioClient(user_name, room)

    # Autenticação
    if text_client.authenticate():
        print("Autenticação concluída!")
        
        # Áudio em segundo plano
        audio_thread = threading.Thread(target=audio_client.start, daemon=True)
        audio_thread.start()

        # Texto em primeiro plano
        text_client.start()
        
    else:
        print("Encerrando cliente devido a falha no login.")

if __name__ == "__main__":
    main()