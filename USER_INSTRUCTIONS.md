# Guia: Configuração do Sistema de Videoconferência em Múltiplos Computadores

Este guia explica como configurar o sistema de videoconferência distribuído em computadores distintos, permitindo comunicação cross-broker entre usuários em diferentes máquinas.

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
# ou: .venv\Scripts\activate  # Windows

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
Edite `src/shared/config.py` em TODAS as máquinas:

```python
# Mude de 127.0.0.1 para os IPs reais
BROKER_LIST = [
    {
        "broker_id": 0,
        "host": "192.168.1.100",  # IP da Máquina A
        "publish_port": 6555,
        "subscribe_port": 6556,
        "auth_port": 6557,
        "broker_pub_port": 6560,
        "broker_sub_port": 6561,
    },
    {
        "broker_id": 1,
        "host": "192.168.1.101",  # IP da Máquina B
        "publish_port": 6565,
        "subscribe_port": 6566,
        "auth_port": 6567,
        "broker_pub_port": 6570,
        "broker_sub_port": 6571,
    },
    {
        "broker_id": 2,
        "host": "192.168.1.102",  # IP da Máquina C
        "publish_port": 6575,
        "subscribe_port": 6576,
        "auth_port": 6577,
        "broker_pub_port": 6580,
        "broker_sub_port": 6581,
    },
]
```

### 2.2 Configurar Firewall
Em cada máquina, libere as portas necessárias:

**Linux (Ubuntu/Debian):**
```bash
# Liberar portas dos brokers
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
```

**Windows (PowerShell como Administrador):**
```powershell
# Liberar portas (exemplo para broker 0)
New-NetFirewallRule -DisplayName "Broker0 XSUB" -Direction Inbound -Protocol TCP -LocalPort 6555 -Action Allow
New-NetFirewallRule -DisplayName "Broker0 XPUB" -Direction Inbound -Protocol TCP -LocalPort 6556 -Action Allow
# ... repetir para todas as portas
```

**macOS:**
```bash
# Verificar se o firewall está ativo
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Adicionar regras (se necessário)
# O macOS geralmente permite conexões locais por padrão
```

## Passo 3: Inicialização dos Brokers

### 3.1 Iniciar Broker na Máquina A (192.168.1.100)
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 0 &
```

### 3.2 Iniciar Broker na Máquina B (192.168.1.101)
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 1 &
```

### 3.3 Iniciar Broker na Máquina C (192.168.1.102)
```bash
cd videoconferencia
source .venv/bin/activate
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 2 &
```

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