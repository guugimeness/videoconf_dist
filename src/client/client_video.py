import cv2
import zmq
import numpy as np
import time
import queue
import threading
import uuid
from dataclasses import dataclass
import sys


# =========================
# CONFIGURAÇÕES
# =========================
VIDEO_FPS = 15
MAX_FRAME_QUEUE = 10
HEARTBEAT_INTERVAL = 2


@dataclass
class ClientConfig:
    user_id: str
    room: str
    broker_host: str = "localhost"
    video_pub_port: int = 5555
    video_sub_port: int = 5556


class VideoClient:
    def __init__(self, config: ClientConfig):
        self.config = config
        self.context = zmq.Context()
        self.running = False

        # canal de envio de vídeo
        self.video_pub = self.context.socket(zmq.PUB)
        self.video_pub.connect(
            f"tcp://{config.broker_host}:{config.video_pub_port}"
        )

        # canal de recepção de vídeo
        self.video_sub = self.context.socket(zmq.SUB)
        self.video_sub.connect(
            f"tcp://{config.broker_host}:{config.video_sub_port}"
        )
        self.video_sub.setsockopt_string(zmq.SUBSCRIBE, config.room)

        # buffer para QoS simples
        self.frame_queue = queue.Queue(maxsize=MAX_FRAME_QUEUE)

        self.capture_thread = None
        self.send_thread = None
        self.recv_thread = None
        self.render_thread = None

        self.remote_frames = {}

    # =========================
    # CONTROLE DE SESSÃO
    # =========================
    def login(self):
        print(f"[LOGIN] Usuário {self.config.user_id} conectado")
        print(f"[ROOM] Entrando na sala {self.config.room}")

    def start(self):
        self.running = True
        self.login()

        self.capture_thread = threading.Thread(target=self.capture_loop)
        self.send_thread = threading.Thread(target=self.send_loop)
        self.recv_thread = threading.Thread(target=self.receive_loop)
        self.render_thread = threading.Thread(target=self.render_loop)

        self.capture_thread.start()
        self.send_thread.start()
        self.recv_thread.start()
        self.render_thread.start()

    def stop(self):
        self.running = False
        self.video_pub.close()
        self.video_sub.close()
        self.context.term()
        print("[STOP] Encerrando cliente de vídeo")

    # =========================
    # THREADS
    # =========================
    def capture_loop(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FPS, VIDEO_FPS)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (320, 240))

            # QoS para vídeo: se a fila estiver cheia, descarta frame antigo
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass

            self.frame_queue.put(frame)
            time.sleep(1 / VIDEO_FPS)

        cap.release()

    def send_loop(self):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]

        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            success, buffer = cv2.imencode('.jpg', frame, encode_param)
            if not success:
                continue

            payload = buffer.tobytes()
            topic = self.config.room
            msg_id = str(uuid.uuid4()).encode()
            timestamp = str(time.time()).encode()

            self.video_pub.send_multipart([
                topic.encode(),
                self.config.user_id.encode(),
                msg_id,
                timestamp,
                payload
            ])

    def receive_loop(self):
            while self.running:
                try:
                    topic, sender, msg_id, timestamp, payload = \
                        self.video_sub.recv_multipart(flags=zmq.NOBLOCK)

                    sender = sender.decode()

                    np_buffer = np.frombuffer(payload, dtype=np.uint8)
                    frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)

                    # só salva se conseguiu decodificar
                    if frame is not None:
                        self.remote_frames[sender] = frame

                except zmq.Again:
                    time.sleep(0.01)

    def render_loop(self):
        while self.running:
            for sender, frame in list(getattr(self, 'remote_frames', {}).items()):
                cv2.imshow(f"Remote - {sender}", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop()
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python client_video.py <user_id> <room>")
        sys.exit(1)

    user_id = sys.argv[1]
    room = sys.argv[2]

    config = ClientConfig(
        user_id=user_id,
        room=room,
        broker_host="localhost"
    )

    client = VideoClient(config)

    try:
        client.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop()

    client = VideoClient(config)

    try:
        client.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop()
