# Guia: Configuração do Sistema de Videoconferência em Múltiplos Computadores

Este guia explica como configurar o sistema de videoconferência distribuído em computadores distintos, permitindo comunicação cross-broker entre usuários em diferentes máquinas.

<<<<<<< HEAD
> **Status do Sistema**: ✅ Testado e validado  
> Todos os componentes foram verificados com sucesso. Consulte `TEST_REPORT.md` para detalhes dos testes.

=======
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
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
<<<<<<< HEAD
# ou: .venv\\Scripts\\activate  # Windows
=======
# ou: .venv\Scripts\activate  # Windows
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8

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
<<<<<<< HEAD
Edite `src/shared/config.py` em TODAS as máquinas para refletir os IPs e portas reais dos brokers.

Exemplo de configuração:
```python
BROKER_LIST = [
    {
        "broker_id": 0,
        "host": "192.168.1.100",
=======
Edite `src/shared/config.py` em TODAS as máquinas:

```python
# Mude de 127.0.0.1 para os IPs reais
BROKER_LIST = [
    {
        "broker_id": 0,
        "host": "192.168.1.100",  # IP da Máquina A
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
        "publish_port": 6555,
        "subscribe_port": 6556,
        "auth_port": 6557,
        "broker_pub_port": 6560,
        "broker_sub_port": 6561,
    },
    {
        "broker_id": 1,
<<<<<<< HEAD
        "host": "192.168.1.101",
=======
        "host": "192.168.1.101",  # IP da Máquina B
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
        "publish_port": 6565,
        "subscribe_port": 6566,
        "auth_port": 6567,
        "broker_pub_port": 6570,
        "broker_sub_port": 6571,
    },
<<<<<<< HEAD
=======
    {
        "broker_id": 2,
        "host": "192.168.1.102",  # IP da Máquina C
        "publish_port": 6575,
        "subscribe_port": 6576,
        "auth_port": 6577,
        "broker_pub_port": 6580,
        "broker_sub_port": 6581,
    },
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
]
```

### 2.2 Configurar Firewall
Em cada máquina, libere as portas necessárias:

**Linux (Ubuntu/Debian):**
```bash
# Liberar portas dos brokers
<<<<<<< HEAD
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
=======
sudo ufw allow 6555/tcp  # Broker 0 XSUB
sudo ufw allow 6556/tcp  # Broker 0 XPUB
sudo ufw allow 6557/tcp  # Broker 0 REP
sudo ufw allow 6560/tcp  # Broker 0 inter-PUB
sudo ufw allow 6561/tcp  # Broker 0 inter-SUB

sudo ufw allow 6565/tcp  # Broker 1 XSUB
sudo ufw allow 6566/tcp  # Broker 1 XPUB
sudo ufw allow 6567/tcp  # Broker 1 REP
sudo ufw allow 6570/tcp  # Broker 1 inter-PUB
sudo ufw allow 6571/tcp  # Broker 1 inter-SUB

sudo ufw allow 6575/tcp  # Broker 2 XSUB
sudo ufw allow 6576/tcp  # Broker 2 XPUB
sudo ufw allow 6577/tcp  # Broker 2 REP
sudo ufw allow 6580/tcp  # Broker 2 inter-PUB
sudo ufw allow 6581/tcp  # Broker 2 inter-SUB
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
```

**Windows (PowerShell como Administrador):**
```powershell
<<<<<<< HEAD
=======
# Liberar portas (exemplo para broker 0)
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
New-NetFirewallRule -DisplayName "Broker0 XSUB" -Direction Inbound -Protocol TCP -LocalPort 6555 -Action Allow
New-NetFirewallRule -DisplayName "Broker0 XPUB" -Direction Inbound -Protocol TCP -LocalPort 6556 -Action Allow
# ... repetir para todas as portas
```

**macOS:**
```bash
<<<<<<< HEAD
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
=======
# Verificar se o firewall está ativo
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Adicionar regras (se necessário)
# O macOS geralmente permite conexões locais por padrão
```

## Passo 3: Inicialização dos Brokers

### 3.1 Iniciar Broker na Máquina A (192.168.1.100)
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 0 &
```

<<<<<<< HEAD
### 5.2 Iniciar Broker na Máquina B
=======
### 3.2 Iniciar Broker na Máquina B (192.168.1.101)
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 1 &
```

<<<<<<< HEAD
### 5.3 Iniciar Broker na Máquina C
=======
### 3.3 Iniciar Broker na Máquina C (192.168.1.102)
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 2 &
```

<<<<<<< HEAD
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
=======
### 3.4 Verificar Brokers Ativos
Em qualquer máquina, verifique se todos os brokers estão rodando:
```bash
# Verificar processos locais
ps aux | grep broker_node

# Verificar conectividade de rede (exemplo)
telnet 192.168.1.100 6555  # Testar broker 0
telnet 192.168.1.101 6565  # Testar broker 1
telnet 192.168.1.102 6575  # Testar broker 2
```

## Passo 4: Conectar Clientes

### 4.1 Cliente de Texto (Recomendado para Teste)
Clientes podem conectar de QUALQUER máquina para QUALQUER broker:

```bash
# Na Máquina A
PYTHONPATH=src python3 src/client/client.py alice SALA_TESTE

# Na Máquina B
PYTHONPATH=src python3 src/client/client.py bob SALA_TESTE

# Na Máquina C
PYTHONPATH=src python3 src/client/client.py charlie SALA_TESTE
```

**Nota:** O usuário será automaticamente direcionado para o broker correto baseado no hash do username, independente da máquina de onde está conectando.

### 4.2 Cliente de Vídeo
```bash
# Máquina A
PYTHONPATH=src python3 src/client/client_video.py alice SALA_VIDEO

# Máquina B
PYTHONPATH=src python3 src/client/client_video.py bob SALA_VIDEO
```

### 4.3 Cliente de Áudio
```bash
# Máquina A
PYTHONPATH=src python3 src/client/client_audio.py alice SALA_AUDIO

# Máquina B
PYTHONPATH=src python3 src/client/client_audio.py bob SALA_AUDIO
```

## Passo 5: Teste de Comunicação Cross-Broker

### 5.1 Teste Básico
1. Conecte `alice` (Máquina A) na `SALA_TESTE`
2. Conecte `bob` (Máquina B) na `SALA_TESTE`
3. Conecte `charlie` (Máquina C) na `SALA_TESTE`

**Resultado esperado:** Todos os usuários conseguem trocar mensagens, mesmo estando em máquinas físicas diferentes.

### 5.2 Verificar Distribuição
Execute em qualquer máquina:
```bash
# Ver qual broker cada usuário está usando
PYTHONPATH=src python3 -c "
from src.shared import broker_discovery
print('alice -> broker', broker_discovery.get_broker_for_user('alice')['broker_id'])
print('bob -> broker', broker_discovery.get_broker_for_user('bob')['broker_id'])
print('charlie -> broker', broker_discovery.get_broker_for_user('charlie')['broker_id'])
"
```

## Passo 6: Monitoramento e Troubleshooting

### 6.1 Logs dos Brokers
Cada broker mostra logs detalhados. Procure por:
```
[BROKER-0] Forwarded message abc123 to broker 1
[BROKER-1] Relayed forwarded message abc123 from broker 0
```

### 6.2 Verificar Conectividade
```bash
# Testar conectividade entre máquinas
ping 192.168.1.100  # Da máquina B para A
ping 192.168.1.101  # Da máquina C para B

# Testar portas específicas
nc -zv 192.168.1.100 6555  # Testar porta do broker 0
```

### 6.3 Problemas Comuns

**Erro: "Connection refused"**
- Verifique se o broker está rodando na máquina correta
- Confirme IPs no config.py
- Verifique firewall

**Erro: "No module named 'zmq'"**
- Ative o ambiente virtual: `source .venv/bin/activate`
- Reinstale dependências: `pip install -r requirements.txt`

**Mensagens não chegam**
- Verifique se usuários estão na mesma sala
- Confirme que todos os 3 brokers estão ativos
- Verifique logs dos brokers por mensagens de encaminhamento

## Passo 7: Encerramento

### 7.1 Parar Brokers
```bash
# Em cada máquina
pkill -f broker_node

# Ou usar script (se configurado)
./stop_cluster.sh
```

### 7.2 Parar Clientes
```bash
# Digite "sair" no terminal do cliente
# Ou mate processos
pkill -f client.py
```

## Configuração Avançada

### Adicionar Mais Brokers
Para adicionar uma 4ª máquina (192.168.1.103):
1. Adicione entrada no `BROKER_LIST` com `broker_id: 3`
2. Configure portas não conflitantes (ex: 6585, 6586, etc.)
3. Libere portas no firewall
4. Inicie: `python3 src/broker/broker_node.py --broker-id 3`

### Balanceamento de Carga
O sistema distribui usuários automaticamente. Para testar balanceamento:
```bash
# Conectar muitos usuários e verificar distribuição
for i in {1..10}; do
    PYTHONPATH=src python3 src/client/client.py "user$i" SALA_TESTE &
done
```

### Segurança
Para produção, considere:
- Usar IPs internos da rede
- Configurar VPN para acesso remoto
- Adicionar autenticação de usuários
- Usar certificados SSL/TLS no ZeroMQ

Este setup permite videoconferência distribuída com failover automático e comunicação cross-broker transparente entre usuários em máquinas diferentes.
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
