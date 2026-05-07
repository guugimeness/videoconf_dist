## Notas de Implementação

- Sistema está em modo cluster por padrão (BROKER_CLUSTER_MODE=True)
- Para modo single-broker: mudar BROKER_CLUSTER_MODE=False em config.py
- Portas devem estar disponíveis antes de iniciar brokers
- Recomenda-se usar 127.0.0.1 para teste local

## Como Usar

###  Iniciar o Sistema

#### Opção 1: Script Automático 
```bash
# Dar permissão de execução
chmod +x start_cluster.sh

# Iniciar cluster completo
./start_cluster.sh
```

#### Opção 2: Inicialização Manual
```bash
# Terminal 1: Broker 0
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 0 &

# Terminal 2: Broker 1
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 1 &

# Terminal 3: Broker 2
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 2 &
```

### Conectar Clientes

**IMPORTANTE**: Sempre use `PYTHONPATH=src` para executar clientes!

```bash
# Cliente de texto (recomendado para teste)
PYTHONPATH=src python3 src/client/client.py alice SALA_A

# Ou executar como módulo Python
PYTHONPATH=src python3 -m client.client alice SALA_A
```

**Exemplos de uso:**
```bash
# Diferentes usuários (serão distribuídos automaticamente)
PYTHONPATH=src python3 src/client/client.py alice SALA_A
PYTHONPATH=src python3 src/client/client.py bob SALA_B
PYTHONPATH=src python3 src/client/client.py charlie SALA_A
```

#### Opção 1: Script de Parada
```bash
# Dar permissão de execução
chmod +x stop_cluster.sh

# Parar tudo
./stop_cluster.sh
```

#### Opção 2: Parada Manual
```bash
# Mata todos os brokers e clientes
pkill -f broker_node
pkill -f client.py

# Ou usar o script de limpeza (se existir)
./stop_cluster.sh
```

#### Parar Componentes Individualmente
```bash
# Parar apenas brokers
pkill -f broker_node

# Parar apenas clientes
pkill -f client.py

# Forçar encerramento (se necessário)
pkill -9 -f broker_node
pkill -9 -f client.py
```
# Ver processos ativos
ps aux | grep -E "(broker_node|client\.py)"

# Se nada aparecer, tudo foi parado
```

##  Solução de Problemas

### Erro: `ModuleNotFoundError: No module named 'shared'`
```bash
# ❌ Errado
python3 src/client/client.py alice SALA_A

# ✅ Correto
PYTHONPATH=src python3 src/client/client.py alice SALA_A
```

### Erro: `ModuleNotFoundError: No module named 'client'`
- Verifique se os arquivos `__init__.py` existem em `src/client/`, `src/broker/`, `src/shared/`
- Use sempre `PYTHONPATH=src`

### Brokers Não Conectam
```bash
# Verificar portas em uso
netstat -tlnp | grep :655

# Liberar portas se necessário
sudo fuser -k 6555/tcp 6556/tcp 6557/tcp
```

### Cliente Não Conecta ao Broker Correto
- Verifique se todos os 3 brokers estão rodando
- Use `ps aux | grep broker_node` para confirmar
- Cliente será automaticamente direcionado pelo hash do username

###  Gerenciamento de Brokers

#### Ver Brokers Ativos
```bash
# Ver todos os processos broker_node em execução
ps aux | grep broker_node

# Ou de forma mais limpa
ps aux | grep "broker_node.py"

# Ver apenas os PIDs
pgrep -f broker_node
```

**Exemplo de saída:**
```
nami  12345  0.0  1.2  ... broker_node.py --broker-id 0
nami  12346  0.0  1.2  ... broker_node.py --broker-id 1
nami  12347  0.0  1.2  ... broker_node.py --broker-id 2
```

#### Matar Todos os Brokers
```bash
# Mata todos os processos broker_node
pkill -f broker_node

# Ou forçar encerramento
pkill -9 -f broker_node

# Verificar se foram mortos
ps aux | grep broker_node
```

#### Matar Um Broker Específico
```bash
# Matar broker com ID 0
pkill -f 'broker_node.py --broker-id 0'

# Matar broker com ID 1
pkill -f 'broker_node.py --broker-id 1'

# Matar broker com ID 2
pkill -f 'broker_node.py --broker-id 2'

# Forçar encerramento de broker específico (se necessário)
pkill -9 -f 'broker_node.py --broker-id 2'
```

#### Reiniciar um Broker Específico
```bash
# 1. Matar o broker
pkill -f 'broker_node.py --broker-id 0'

# 2. Esperar 1 segundo
sleep 1

# 3. Iniciar novamente
python3 src/broker/broker_node.py --broker-id 0 &
```

##  Características Técnicas

### Distribuição Consistente
- Usa hash MD5 do username
- Garante que mesmo usuário sempre vai para o mesmo broker
- Fórmula: `broker_id = hash(username) % num_brokers`

### Comunicação Inter-Broker
- PUB/SUB com prefixo `INTER_BROKER:`
- Sincronização de eventos LOGIN/LOGOUT
- Transmissão de presença global entre brokers

### Reconexão e Fallback
- Max 5 tentativas de autenticação
- Max 5 tentativas de reconexão
- Fallback automático para próximo broker
- Backoff exponencial

### Sincronização de Presença
- Cada broker conhece todos os usuários online
- Timeout de 30 segundos para inatividade
- Limpeza automática de sessões expiradas

## Componentes Principais

1. **src/shared/config.py**
   - Configuração de cluster mode (True/False)
   - Lista de brokers com portas específicas
   - Portas para cada broker:
     - XSUB (publish): 6555, 6565, 6575
     - XPUB (subscribe): 6556, 6566, 6576
     - REP (auth): 6557, 6567, 6577
     - Inter-broker PUB: 6560, 6570, 6580
     - Inter-broker SUB: 6561, 6571, 6581

2. **src/shared/broker_discovery.py**
   - Descoberta automática de brokers
   - Distribuição por hash consistente: `hash(username) % num_brokers`
   - Seleção de broker de fallback
   - Validação de configuração

3. **src/broker/broker_node.py**
   - Implementação de broker cluster-aware
   - Comunicação inter-broker via PUB/SUB
   - Sincronização global de usuários
   - Prevenção de nomes duplicados
   - Heartbeat e limpeza de sessões inativas

4. **src/client/client.py**
   - Descoberta dinâmica de broker
   - Inicialização de clientes (text, audio, video)

5. **src/client/client_text.py, client_audio.py, client_video.py**
   - Reconexão automática
   - Fallback para outros brokers em caso de falha
   - Sincronização com broker primário