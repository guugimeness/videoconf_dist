# Documentação Técnica - Sistema de Videoconferência Distribuído

## Índice
1. Visão Geral
2. Arquitetura do Sistema
3. Componentes Detalhados
4. Padrões ZeroMQ
5. Estratégias de Tolerância a Falhas
6. Guia de Deployment

---

## Visão Geral

O Sistema de Videoconferência Distribuído é uma aplicação Python que permite comunicação em tempo real com suporte a **áudio**, **vídeo** e **texto** através de uma arquitetura descentralizada baseada em **ZeroMQ**.

**Características principais:**
- ✅ Comunicação ponto-a-ponto com broker central
- ✅ Suporte simultâneo de múltiplas mídias
- ✅ Isolamento de processos por sala
- ✅ Reconexão automática com backoff exponencial
- ✅ QoS (Quality of Service) com retry
- ✅ Monitoramento de sessão com heartbeat
- ✅ Compressão de mídia (int16 para áudio, JPEG para vídeo)

---

## Arquitetura do Sistema

### Modelo Geral

<p align="center">
  <img src="https://github.com/guugimeness/videoconf_dist/blob/32fef5fd9db93aa47488a51565865f440d3f70c3/docs/diagrama-arquitetura.jpeg" alt="Image">
</p>

### Camadas de Comunicação

#### **Camada 1: Autenticação (REQ/REP)**
- Port: `5557`
- Padrão: **ROUTER/DEALER** (via REQ/REP)
- Responsabilidade: Validar login e registrar sessão
- Timeout: Síncrono

#### **Camada 2: Transmissão de Dados (PUB/SUB)**
- Frontend (XSUB): `5555` - Recebe de clientes
- Backend (XPUB): `5556` - Distribui para subscribers
- Padrão: **PUB/SUB Proxy** (XSUB/XPUB)
- Responsabilidade: Broker ativo com filtragem por topic

---

## Componentes Detalhados

### **1. Broker Central**

**Arquivo:** `src/broker/broker_central.py`

**Responsabilidades:**
- Roteamento de mensagens (XSUB/XPUB proxy)
- Autenticação e validação de sessão (REQ/REP)
- Gerenciamento de timeout de usuários
- Injeção de mensagens de sistema

**Portas:**
| Porta | Socket | Uso |
|-------|--------|-----|
| 5555 | XSUB | Recebe de PUBs |
| 5556 | XPUB | Envia para SUBs |
| 5557 | REP | Login/Autenticação |

---

### **2. Cliente de Texto**

**Arquivo:** `src/client/client_text.py`

**Threads:**
1. **Captura** - Lê input do usuário
2. **Envio** - PUB com heartbeat e QoS
3. **Recepção** - SUB com watchdog
4. **Renderização** - Exibe mensagens com prompt

**Padrões:**
- PUB/SUB para chat
- REQ/REP para autenticação
- Queue para IPC entre threads

---

### **3. Cliente de Áudio**

**Arquivo:** `src/client/client_audio.py`

**Threads:**
1. **Captura** - sounddevice callback (16-bit PCM)
2. **Envio** - PUB ao broker (com reconexão)
3. **Recepção** - SUB do broker (filtra próprio áudio)
4. **Playback** - sounddevice output (reproduz jitter buffer)
5. **Heartbeat** - Monitora saúde
6. **Stats** - Log de métricas

**Compressão:**
- Input: float32 [-1, 1] → Output: int16 [-32768, 32767]
- Redução: ~50% da largura de banda

---

### **4. Cliente de Vídeo**

**Arquivo:** `src/client/client_video.py`

**Threads:**
1. **Captura** - OpenCV (320×240@15fps)
2. **Envio** - PUB em multipart com JPEG
3. **Recepção** - SUB com timeout de 5s
4. **Renderização** - Grid adaptável (sqrt layout)
5. **Limpeza** - Remove frames expirados

---

### **5. Config Centralizada** ⚙️

**Arquivo:** `src/shared/config.py`

```python
BROKER_HOST = "172.20.10.9"
PUBLISH_PORT = 5555
SUBSCRIBE_PORT = 5556
AUTH_PORT = 5557
VIDEO_CAMERA_INDEX = 1

AUDIO_INPUT_DEVICE = 0
AUDIO_OUTPUT_DEVICE = 0
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 1
```

---

## Padrões ZeroMQ

### 1. **PUB/SUB Proxy (XSUB/XPUB)** - Camada de Dados

**Localização:** `src/broker/broker_central.py`

```python
# Frontend: Recebe de Publishers (Clientes)
frontend = context.socket(zmq.XSUB)
frontend.bind(f"tcp://*:{XSUB_PORT}")  # 5555

# Backend: Distribui para Subscribers (Clientes)
backend = context.socket(zmq.XPUB)
backend.bind(f"tcp://*:{XPUB_PORT}")   # 5556

# Relay: Encaminha mensagens do frontend → backend
backend.send_multipart(parts)
```

**Fluxo:**
```
Cliente (PUB)
     ↓ send("SALA_A:TEXTO:user1:uuid|Olá")
Broker (XSUB)
     ↓ recv_multipart()
Broker (XPUB)
     ↓ send_multipart()
Cliente (SUB) → recebe se subscriber de "SALA_A:TEXTO:"
```

**Topologia de Subscriptions:**

Os clientes assinam tópicos específicos:
- `{SALA}:TEXTO:` - Mensagens de chat
- `{SALA}:AUDIO:` - Frames de áudio
- `{SALA}:HEARTBEAT:` - Pings de saúde

---

### 2. **REQ/REP** - Autenticação

**Localização:** `src/broker/broker_central.py` e `src/client/client_text.py`

```python
# SERVIDOR (Broker)
auth_socket = context.socket(zmq.REP)
auth_socket.bind(f"tcp://*:{AUTH_PORT}")  # 5557

request = auth_socket.recv_string()  # "LOGIN|SALA_A|user1"
auth_socket.send_string("OK" ou "ERRO")

# CLIENTE
socket_req = context.socket(zmq.REQ)
socket_req.connect(f"tcp://{cfg.BROKER_HOST}:{cfg.AUTH_PORT}")
socket_req.send_string(f"LOGIN|{self.room}|{self.user_name}")
resposta = socket_req.recv_string()
```

**Características:**
- ✅ Síncrono e bloqueante
- ✅ Garante entrega (request → reply)
- ✅ Validação de nome único
- ✅ Inicialização de sessão

---

### 3. **Formato de Mensagens Multipart**

#### **Texto/Áudio/Heartbeat (1 parte):**
```
"SALA_A:TEXTO:user1:abc123|Olá pessoal"
 └─ Header ─┘             └─ Payload ─┘
```

#### **Vídeo (5 partes):**
```python
[
  room.encode(),              # Part 0: "SALA_A"
  user_id.encode(),           # Part 1: "user1"
  msg_id,                     # Part 2: UUID
  timestamp,                  # Part 3: Unix timestamp
  payload                     # Part 4: JPEG bytes
]
```

**Motivo:** Vídeo usa multipart para melhor controle sobre metadados e payload binário.

---

## Estratégias de Tolerância a Falhas

### 1. **Heartbeat com Watchdog**

**Implementação:** `src/client/client_text.py` - linhas 124-137

```python
HEARTBEAT_INTERVAL = 3    # Envia ping a cada 3s
HEARTBEAT_TIMEOUT = 10    # Reconecta se 10s sem receber

# Sender Thread
if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
    hb_msg = f"{self.room}:HEARTBEAT:{self.user_name}:0|ping"
    socket_pub.send_string(hb_msg)
    last_heartbeat = time.time()

# Receiver Thread
try:
    message = socket_sub.recv_string()
    self.last_recv_time = time.time()  # Reseta watchdog
except zmq.error.Again:  # Timeout
    if time.time() - self.last_recv_time > HEARTBEAT_TIMEOUT:
        self.reconnect_event.set()
```

**Benefício:** Detecta broker offline em até 10 segundos.

---

### 2. **Reconexão com Backoff Exponencial**

**Implementação:** `src/client/client_audio.py` - linhas 96-117

```python
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 2  # segundos

reconnect_count = 0

while not self.stop_event.is_set():
    try:
        # Tenta conectar
        socket = context.socket(zmq.PUB)
        socket.connect(addr)
        reconnect_count = 0  # Reset
        
    except Exception as e:
        reconnect_count = min(reconnect_count + 1, MAX_RECONNECT_ATTEMPTS)
        delay = RECONNECT_DELAY * (2 ** (reconnect_count - 1))
        # delay: 2s → 4s → 8s → 16s → 32s
        time.sleep(delay)
```

**Sequência:**
```
Tentativa 1: Falha → Aguarda 2s
Tentativa 2: Falha → Aguarda 4s
Tentativa 3: Falha → Aguarda 8s
Tentativa 4: Falha → Aguarda 16s
Tentativa 5: Falha → Aguarda 32s
Tentativa 6+: Continua tentando a cada 32s
```

---

### 3. **QoS com Retry**

**Implementação:** `src/client/client_text.py` - linhas 139-154

```python
RETRY_TIMEOUT = 5  # segundos

# Sender: Armazena mensagens pendentes
self.pending_messages[msg_id] = (msg, time.time())

# Receiver: Aguarda ACK (recebimento da própria mensagem)
if sender == self.user_name:
    # Se recebi minha mensagem de volta, chegou no broker!
    del self.pending_messages[msg_id]

# Sender: Reenvia se não receber ACK em 5s
for msg_id, (msg, timestamp) in list(self.pending_messages.items()):
    if current_time - timestamp > RETRY_TIMEOUT:
        socket_pub.send_string(msg)  # Reenvia
```

**Fluxo:**
```
Cliente envisa: "Olá" (msg_id: abc123, time: 10:00:00)
└─ Armazena em pending_messages

Broker recebe e retransmite
└─ Cliente recebe sua própria mensagem (ACK implícito)

Se receber → Remove de pending
Se NÃO receber em 5s → Reenvia
```

---

### 4. **Session Timeout**

**Implementação:** `src/broker/broker_central.py` - linhas 99-113

```python
SESSION_TIMEOUT = 30  # segundos

# Broker atualiza timestamp a cada mensagem recebida
if sender_name in active_users:
    active_users[sender_name]["last_seen"] = current_time

# Periodicamente verifica timeouts
for user, info in active_users.items():
    if current_time - info["last_seen"] > SESSION_TIMEOUT:
        dead_users.append(user)

# Remove e notifica
for user in dead_users:
    del active_users[user]
    aviso = f"{sala}:TEXTO:SISTEMA:0|Usuário '{user}' desconectou."
    backend.send(aviso.encode('utf-8'))
```

**Cenários:**
- Usuário fecha app → Não envia heartbeat → Timeout em 30s
- Usuário envia mensagem → Timestamp atualizado
- Broker libera nome para reutilização

---

### 5. **Jitter Buffer**

**Implementação:** `src/client/client_audio.py` - linhas 35-37

```python
from collections import deque

JITTER_BUFFER_SIZE = 10  # Armazena até 10 frames

self.jitter_buffer = deque(maxlen=JITTER_BUFFER_SIZE)
self.jitter_lock = threading.Lock()
```

**Benefício:** Absorve variações de latência de rede, suavizando áudio entrecortado.

---

### 6. **Thread-Safe Queues**

**Implementação:** `src/client/client_text.py` - linhas 20-22

```python
import queue
import threading

self.send_queue = queue.Queue()      # Thread-safe
self.render_queue = queue.Queue()    # Thread-safe
self.pending_lock = threading.Lock() # Sincronização explícita

# Uso
with self.pending_lock:
    self.pending_messages[msg_id] = (msg, time.time())
```

**Protege:** Evita race conditions entre threads de captura, envio, recepção.

---

### 7. **Compressão de Mídia**

#### **Áudio: int16 (50% redução)**
```python
# Float32 [-1, 1] → int16 [-32768, 32767]
audio_data = np.clip(indata * 32767, -32768, 32767).astype(np.int16)
socket.send(topic + audio_data.tobytes())
```

#### **Vídeo: JPEG (90% redução)**
```python
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
success, buffer = cv2.imencode(".jpg", frame, encode_param)
socket.send_multipart([..., buffer.tobytes()])
```

---

## Guia de Deployment

### **1. Configurar Hardware**

```bash
# Detectar dispositivos de áudio
python audio_device.py

# Selecionar IDs de entrada/saída
# Atualizar src/shared/config.py
```

### **2. Build Docker**

```bash
docker build -t videoconf .
```

### **3. Iniciar Broker**

```bash
docker-compose up broker
# Espera: "[BROKER] Iniciando broker ativo..."
```

### **4. Iniciar Clientes** (em terminais diferentes)

```bash
# Terminal 2
cd src && python -m client.client user1 SALA_A

# Terminal 3
cd src && python -m client.client user2 SALA_A
```

### **5. Teste de Comunicação**

```
[user1]: Olá user2!
[user2]: Oi user1! Tudo bem?
```
