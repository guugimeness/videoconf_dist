# Documentação Técnica - Sistema de Videoconferência Distribuído

## Integrantes do Grupo B 

Eduardo Sanzovo Quaggio      - 813641
Fernanda Nami Aramaki        - 791969
Gustavo de Oliveira Gimenes  - 820759
Leonardo Ryuiti Miasiro      - 800983
Nicole Brito Cardoso         - 812078

## Índice
1. Visão Geral
2. Arquitetura do Sistema
3. Componentes Detalhados
4. Padrões ZeroMQ
5. Estratégias de Tolerância a Falhas
6. Guia de Deployment

---

## Visão Geral

O Sistema de Videoconferência Distribuído é uma aplicação Python que permite comunicação em tempo real com suporte a **áudio**, **vídeo** e **texto**. Ele utiliza uma arquitetura distribuída baseada em múltiplos brokers cooperando entre si. 

Cada broker é responsável por gerenciar um subconjunto de usuários e salas, permitindo escalabilidade horizontal, balanceamento de carga e tolerância a falhas.

Os brokers comunicam-se através de canais **ZeroMQ** dedicados para sincronização de presença, encaminhamento de mensagens e monitoramento de sessões.

**Características principais:**
- ✅ Arquitetura distribuída com múltiplos brokers
- ✅ Comunicação inter-broker via ZeroMQ
- ✅ Descoberta dinâmica de brokers
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

O sistema utiliza uma arquitetura distribuída baseada em múltiplos brokers independentes e cooperativos. Cada broker é responsável por gerenciar um subconjunto de clientes, incluindo autenticação, distribuição de mensagens e controle de sessão.

Os brokers comunicam-se entre si através de canais ZeroMQ dedicados para sincronização de usuários, encaminhamento de mensagens e monitoramento de presença global.

Os clientes conectam-se dinamicamente a um broker utilizando mecanismos de descoberta de serviços implementados pelo sistema.



---

## Componentes Detalhados

### **1. Broker Distribuído**

**Arquivo:** `src/broker/broker_node.py`

**Responsabilidades:**
- Receber mensagens publicadas pelos clientes 
- Distribuir mensagens para clientes inscritos na mesma sala
- Autenticar usuários através de socket REP
- Gerenciar sessões locais dos usuários conectados
- Sincronizar presença dos usuários com os demais brokers
- Encaminhar mensagens para brokers remotos
- Evitar loops de mensagens distribuídas utilizando identificadores únicos
- Remover usuários inativos após timeout


**Sockets utilizados:**
| Socket | Uso |
|-------|-------------|
| XSUB | Recebimento |
| XPUB | Distribuição |
| REP | Autenticação |
| PUB | Encaminhamento |
| SUB | Sincronização |

---

### **2. Cliente de Texto**

**Arquivo:** `src/client/client_text.py`

**Threads:**
1. **Captura** - Lê input do usuário
2. **Envio** - PUB com heartbeat, QoS e reconexão
3. **Recepção** - SUB com watchdog e failover
4. **Renderização** - Exibe mensagens com prompt

**Padrões:**
- PUB/SUB para chat
- REQ/REP para autenticação
- Queue para IPC entre threads
- Discovery/Fallback para seleção de brokers

---

### **3. Cliente de Áudio**

**Arquivo:** `src/client/client_audio.py`

**Threads:**
1. **Captura** - sounddevice callback (16-bit PCM)
2. **Envio** - PUB ao broker com reconexão e failover
3. **Recepção** - SUB do broker com failover automático
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
2. **Envio** - PUB multipart com reconexão e failover
3. **Recepção** - SUB com timeout e failover
4. **Renderização** - Grid adaptável (sqrt layout)
5. **Limpeza** - Remove frames expirados

---

### **5. Config Compartilhada** ⚙️

**Arquivo:** `src/shared/config.py`

**Responsabilidades:**

- Centralizar parâmetros de configuração do sistema
- Definir os brokers disponíveis no cluster
- Configurar portas de comunicação
- Configurar discovery e registry
- Configurar parâmetros de áudio e vídeo
- Definir heartbeat e timeouts

A configuração do cluster é baseada em uma lista de brokers, onde cada um possui portas específicas para publicação, assinatura, autenticação e sincronização entre brokers.

```python
BROKER_CLUSTER_MODE = True

BROKER_LIST = [
    {
        "broker_id": 0,
        "host": "127.0.0.1",
        "publish_port": 6555,
        "subscribe_port": 6556,
        "auth_port": 6557,
    }
]
```

---

## Padrões ZeroMQ

### 1. **PUB/SUB com XSUB/XPUB** 

**Localização:** `src/broker/broker_node.py`

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

Os clientes utilizam sockets PUB para envio de mensagens ao broker e sockets SUB para recebimento dos tópicos assinados. 

**Topologia de Subscriptions:**

Os clientes assinam tópicos específicos:
- `{SALA}:TEXTO:` - Mensagens de chat
- `{SALA}:AUDIO:` - Frames de áudio
- `{SALA}:HEARTBEAT:` - Pings de saúde

---

### 2. **PUB/SUB** - Inter-broker 

**Localização:** `src/broker/broker_node.py`

Os brokers utilizam sockets PUB/SUB adicionais para comunicação distribuída entre os nós do cluster.

Mensagens inter-broker são utilizadas para:

- Sincronização de presença global;
- Propagação de login/logout;
- Encaminhamento de mensagens entre brokers;
- Atualização de heartbeat distribuído.

Cada broker publica eventos para os demais brokers do cluster e também assina eventos vindos dos outros brokers.

### 3. **REQ/REP** - Autenticação

**Localização:** `src/broker/broker_node.py` e `src/client/client_text.py`

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

### 4. **Formato de Mensagens Multipart**

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

**Motivo:** Formato multipart facilita o transporte de informações como sala, usuário, timestamp e payload binário de forma separada, simplificando o encaminhamento das mensagens no sistema. 

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

### 3. **Failover entre brokers**

**Implementação:** `src/shared/broker_discovery.py`

Quando um broker deixa de responder, os clientes tentam selecionar automaticamente um broker alternativo disponível no cluster.

A seleção de brokers alternativos é realizada pela função de fallback do sistema de discovery, permitindo reconexão automática sem necessidade de reinicialização manual do cliente.

O mecanismo de failover é utilizado pelos clientes de texto, áudio e vídeo.

**Fluxo:**

- Cliente detecta falha de conexão
- Sistema inicia tentativas de reconexão
- Após exceder o limite de tentativas, um broker alternativo é selecionado
- Os sockets ZeroMQ são recriados utilizando o novo broker
- O cliente reconecta automaticamente à sala

### 4. **QoS com Retry**

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
Cliente envia: "Olá" (msg_id: abc123, time: 10:00:00)
└─ Armazena em pending_messages

Broker recebe e retransmite
└─ Cliente recebe sua própria mensagem (ACK implícito)

Se receber → Remove de pending
Se NÃO receber em 5s → Reenvia
```

---

### 5. **Session Timeout**

**Implementação:** `src/broker/broker_node.py` - linhas 99-113

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

### 6. **Jitter Buffer**

**Implementação:** `src/client/client_audio.py` - linhas 35-37

```python
from collections import deque

JITTER_BUFFER_SIZE = 10  # Armazena até 10 frames

self.jitter_buffer = deque(maxlen=JITTER_BUFFER_SIZE)
self.jitter_lock = threading.Lock()
```

**Benefício:** Absorve variações de latência de rede, suavizando áudio entrecortado.

---

### 7. **Thread-Safe Queues**

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

### 8. **Compressão de Mídia**

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

### **3. Iniciar cluster**

```bash
./start_cluster.sh
# Iniciando cluster de brokers...
# Iniciando Broker 0
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
