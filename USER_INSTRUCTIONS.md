# Guia: Configuração do Sistema de Videoconferência em Múltiplos Computadores

Este guia explica como configurar o sistema de videoconferência distribuído em computadores distintos, permitindo comunicação cross-broker entre usuários em diferentes máquinas.

> **Status do Sistema**: ✅ Testado e validado  
> Todos os componentes foram verificados com sucesso. Consulte `TEST_REPORT.md` para detalhes dos testes.

## Pré-requisitos

### Hardware/Software Necessário
- **3 computadores** (ou mais) com Linux/Windows/macOS
- **Python 3.8+** instalado em cada máquina
- **Conexão de rede** entre os computadores (mesma rede local)
- **Portas liberadas** no firewall (veja seção de configuração)

### Dependências por Máquina
Cada computador precisa dos mesmos componentes:
- Python 3.8+
- Git (para clonar o repositório)
- Sistema de áudio/vídeo (microfone, câmera)

## Passo 1: Preparação das Máquinas

### 1.1 Clonagem do Repositório
Em cada computador, execute:
```bash
# Clonar o repositório
git clone <URL_DO_REPOSITORIO> videoconferencia
cd videoconferencia

# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou: .venv\\Scripts\\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 1.2 Verificar IPs da Rede
Em cada computador, verifique o IP local:
```bash
# Linux/macOS
ip addr show | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig
```

**Exemplo de saída:**
- **Máquina A**: 192.168.1.100
- **Máquina B**: 192.168.1.101
- **Máquina C**: 192.168.1.102

## Passo 2: Configuração da Rede

### 2.1 Configurar IPs no config.py
Edite `src/shared/config.py` em TODAS as máquinas para refletir os IPs e portas reais dos brokers.

Exemplo de configuração:
```python
BROKER_LIST = [
    {
        "broker_id": 0,
        "host": "192.168.1.100",
        "publish_port": 6555,
        "subscribe_port": 6556,
        "auth_port": 6557,
        "broker_pub_port": 6560,
        "broker_sub_port": 6561,
    },
    {
        "broker_id": 1,
        "host": "192.168.1.101",
        "publish_port": 6565,
        "subscribe_port": 6566,
        "auth_port": 6567,
        "broker_pub_port": 6570,
        "broker_sub_port": 6571,
    },
]
```

### 2.2 Configurar Firewall
Em cada máquina, libere as portas necessárias:

**Linux (Ubuntu/Debian):**
```bash
# Liberar portas dos brokers
sudo ufw allow 6555/tcp
sudo ufw allow 6556/tcp
sudo ufw allow 6557/tcp
sudo ufw allow 6560/tcp
sudo ufw allow 6561/tcp

sudo ufw allow 6565/tcp
sudo ufw allow 6566/tcp
sudo ufw allow 6567/tcp
sudo ufw allow 6570/tcp
sudo ufw allow 6571/tcp

sudo ufw allow 6575/tcp
sudo ufw allow 6576/tcp
sudo ufw allow 6577/tcp
sudo ufw allow 6580/tcp
sudo ufw allow 6581/tcp
```

**Windows (PowerShell como Administrador):**
```powershell
New-NetFirewallRule -DisplayName "Broker0 XSUB" -Direction Inbound -Protocol TCP -LocalPort 6555 -Action Allow
New-NetFirewallRule -DisplayName "Broker0 XPUB" -Direction Inbound -Protocol TCP -LocalPort 6556 -Action Allow
# ... repetir para todas as portas
```

**macOS:**
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

## Passo 3: Configuração de Descoberta Dinâmica

O sistema agora suporta descoberta automática de brokers. Edite `src/shared/config.py` para escolher o modo que deseja usar.

```python
SERVICE_DISCOVERY_MODE = "broadcast"  # Opções: static, registry, broadcast, hybrid
ENABLE_UDP_BROADCAST = True
UDP_BROADCAST_PORT = 9999
REGISTRY_HOST = "192.168.1.100"
REGISTRY_PORT = 8888
REGISTRY_HEARTBEAT_INTERVAL = 60
REGISTRY_TIMEOUT = 180
```

### Quando usar cada modo
- `static`: usa somente a lista fixa `BROKER_LIST`
- `broadcast`: usa UDP broadcast local para descobrir brokers automaticamente
- `registry`: usa um serviço central de registry para listar brokers ativos
- `hybrid`: combina registry + UDP broadcast + fallback estático

## Passo 4: Inicializar o Registry (se aplicável)

Se usar `registry` ou `hybrid`, inicie o registry em uma máquina principal (por exemplo, Máquina A):

```bash
PYTHONPATH=src python3 -m src.broker.registry_server
```

Esse serviço mantém a lista de brokers ativos e responde a consultas de discovery.

## Passo 5: Inicialização dos Brokers

### 5.1 Iniciar Broker na Máquina A
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 0 &
```

### 5.2 Iniciar Broker na Máquina B
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 1 &
```

### 5.3 Iniciar Broker na Máquina C
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 2 &
```

### 5.4 Verificar Brokers Ativos
```bash
ps aux | grep broker_node
nc -zv 192.168.1.100 6555
nc -zv 192.168.1.101 6565
nc -zv 192.168.1.102 6575
```

## Passo 6: Testes Automatizados

Antes de conectar clientes, verifique se o sistema está operacional executando os testes automatizados:

### 6.1 Teste de Sistema
Execute este teste para validar configuração, descoberta e conectividade:

```bash
cd videoconferencia
source .venv/bin/activate
python3 test_system.py
```

**Resultado esperado:**
```
Socket Binding.......................... ✓ PASSED
Broker Selection........................ ✓ PASSED
UDP Discovery........................... ✓ PASSED
Registry................................ ✓ PASSED

Total: 4/4 tests passed
🎉 All tests passed! System is ready.
```

### 6.2 Teste de Integração
Execute este teste para validar roteamento de usuários e conectividade:

```bash
cd videoconferencia
source .venv/bin/activate
python3 test_integration.py
```

**Resultado esperado:**
```
Multi-User Routing...................... ✓ PASSED
PUB/SUB Connectivity.................... ✓ PASSED
```

## Passo 7: Verificação Manual de Discovery (Opcional)

Se desejar testar manualmente a descoberta de brokers:

### 7.1 Testar Broadcast UDP
No computador B, execute:

```bash
python3 - <<'PY'
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 9999))
sock.settimeout(35)
try:
    data, addr = sock.recvfrom(4096)
    print('Recebido de', addr)
    print(json.loads(data.decode()))
except socket.timeout:
    print('Nenhum broadcast recebido')
finally:
    sock.close()
PY
```

### 7.2 Testar Registry
Se estiver usando `registry` ou `hybrid`:

```bash
python3 - <<'PY'
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("192.168.18.18", 8888))
request = {"action": "get_brokers", "timestamp": 0}
sock.send(json.dumps(request).encode())
print(sock.recv(4096).decode())
sock.close()
PY
```

## Passo 8: Conectar Clientes

### 8.1 Cliente de Texto
```bash
PYTHONPATH=src python3 src/client/client.py alice SALA_TESTE
PYTHONPATH=src python3 src/client/client.py bob SALA_TESTE
PYTHONPATH=src python3 src/client/client.py charlie SALA_TESTE
```

### 8.2 Cliente de Vídeo
```bash
PYTHONPATH=src python3 src/client/client_video.py alice SALA_VIDEO
PYTHONPATH=src python3 src/client/client_video.py bob SALA_VIDEO
```

### 8.3 Cliente de Áudio
```bash
PYTHONPATH=src python3 src/client/client_audio.py alice SALA_AUDIO
PYTHONPATH=src python3 src/client/client_audio.py bob SALA_AUDIO
```

## Passo 9: Teste de Comunicação Cross-Broker

1. Conecte `alice` na Máquina A em `SALA_TESTE`
2. Conecte `bob` na Máquina B em `SALA_TESTE`
3. Conecte `charlie` na Máquina C em `SALA_TESTE`

**Resultado esperado:** usuários trocam mensagens com brokers diferentes.

### Verificar qual broker cada usuário usa
```bash
PYTHONPATH=src python3 - <<'PY'
from shared import broker_discovery
print('alice ->', broker_discovery.get_broker_for_user('alice')['broker_id'])
print('bob ->', broker_discovery.get_broker_for_user('bob')['broker_id'])
print('charlie ->', broker_discovery.get_broker_for_user('charlie')['broker_id'])
PY
```

## Passo 10: Monitoramento e Troubleshooting

### 9.1 Logs dos Brokers
Procure por mensagens de encaminhamento e registro de broker:
```
[BROKER-0] ✓ UDP broadcast discovery started
[BROKER-0] ✓ Registered with registry
[BROKER-0] ✓ Registry heartbeat sent
```

### 9.2 Verificar Conectividade
```bash
ping 192.168.1.100
ping 192.168.1.101
nc -zv 192.168.1.100 6555
```

### 9.3 Problemas Comuns

**Connection refused**
- O broker pode não estar rodando
- IPs no `config.py` podem estar errados
- Firewall pode estar bloqueando portas

**No module named 'zmq'**
- Ative o ambiente virtual: `source .venv/bin/activate`
- Reinstale dependências: `pip install -r requirements.txt`

**Nenhum broadcast UDP recebido**
- Verifique se `SERVICE_DISCOVERY_MODE = "broadcast"`
- Confirme `ENABLE_UDP_BROADCAST = True`
- Verifique se a rede permite broadcast UDP

## Passo 11: Encerramento

### 10.1 Parar Brokers
```bash
pkill -f broker_node
```

### 10.2 Parar Registry
```bash
pkill -f registry_server
```
