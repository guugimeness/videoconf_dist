import cv2
import zmq
import numpy as np
import time
import queue
import threading
import uuid
from dataclasses import dataclass
import sys
import platform

# =========================
# CONFIGURAÇÕES
# =========================
VIDEO_FPS = 15
MAX_FRAME_QUEUE = 10

@dataclass
class ClientConfig:
    user_id: str
    room: str
    broker_host: str = "localhost"
    video_pub_port: int = 5555
    video_sub_port: int = 5556
    camera_index: int = 0


class VideoClient:
    def __init__(self, config: ClientConfig):
        self.config = config
        self.context = zmq.Context()
        self.running = False

        # envio
        self.video_pub = self.context.socket(zmq.PUB)
        self.video_pub.connect(
            f"tcp://{config.broker_host}:{config.video_pub_port}"
        )

        # recepção
        self.video_sub = self.context.socket(zmq.SUB)
        self.video_sub.connect(
            f"tcp://{config.broker_host}:{config.video_sub_port}"
        )
        self.video_sub.setsockopt_string(zmq.SUBSCRIBE, config.room)

        self.frame_queue = queue.Queue(maxsize=MAX_FRAME_QUEUE)
        self.remote_frames = {}
        self.lock = threading.Lock()

    def start(self):
        self.running = True

        print(f"[LOGIN] {self.config.user_id}")
        print(f"[ROOM] {self.config.room}")
        print(f"[BROKER] {self.config.broker_host}")
        print(f"[CAMERA] índice {self.config.camera_index}")

        threading.Thread(target=self.capture_loop).start()
        threading.Thread(target=self.send_loop).start()
        threading.Thread(target=self.receive_loop).start()
        threading.Thread(target=self.render_loop).start()

    def stop(self):
        self.running = False
        self.video_pub.close()
        self.video_sub.close()
        self.context.term()
        print("[STOP] Cliente encerrado")

    def capture_loop(self):
        # backend específico para Linux
        if platform.system() == "Linux":
            cap = cv2.VideoCapture(self.config.camera_index, cv2.CAP_V4L2)
        else:
            cap = cv2.VideoCapture(self.config.camera_index)

        if not cap.isOpened():
            print(f"[ERRO] Não foi possível abrir a câmera no índice {self.config.camera_index}")
            self.running = False
            return

        cap.set(cv2.CAP_PROP_FPS, VIDEO_FPS)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (320, 240))

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

            self.video_pub.send_multipart([
                self.config.room.encode(),
                self.config.user_id.encode(),
                str(uuid.uuid4()).encode(),
                str(time.time()).encode(),
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

                if frame is not None:
                    with self.lock:
                        self.remote_frames[sender] = frame

            except zmq.Again:
                time.sleep(0.01)

    def render_loop(self):
        while self.running:
            with self.lock:
                for sender, frame in self.remote_frames.items():
                    cv2.imshow(f"Remote - {sender}", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop()
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python client_video.py <user_id> <room> <broker_host> [camera_index]")
        sys.exit(1)

    user_id = sys.argv[1]
    room = sys.argv[2]
    broker_host = sys.argv[3]
    camera_index = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    config = ClientConfig(
        user_id=user_id,
        room=room,
        broker_host=broker_host,
        camera_index=camera_index
    )

    client = VideoClient(config)

    try:
        client.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop()
