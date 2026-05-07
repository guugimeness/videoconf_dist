#!/bin/bash
# QUICK START: Arquitetura Distribuída com Múltiplos Brokers

echo "🚀 Iniciando cluster de brokers..."
echo ""

# Terminal 1: Broker 0
echo "Iniciando Broker 0 (porta 6555-6557)..."
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 0 &
PID0=$!
sleep 1

# Terminal 2: Broker 1
echo "Iniciando Broker 1 (porta 6565-6567)..."
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 1 &
PID1=$!
sleep 1

# Terminal 3: Broker 2
echo "Iniciando Broker 2 (porta 6575-6577)..."
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 2 &
PID2=$!
sleep 2

echo ""
echo "✅ Cluster iniciado com sucesso!"
echo ""
echo "PIDs dos brokers:"
echo "  Broker 0: $PID0"
echo "  Broker 1: $PID1"
echo "  Broker 2: $PID2"
echo ""
echo "Para conectar um cliente, em outro terminal execute:"
echo "  PYTHONPATH=src python3 -m client.client <username> <room>"
echo ""
echo "Exemplo:"
echo "  PYTHONPATH=src python3 -m client.client alice SALA_A"
echo ""
echo "Para parar todos os brokers:"
echo "  pkill -f broker_node"
echo ""
echo "Ou use o script de parada:"
echo "  ./stop_cluster.sh"
echo ""

# Aguardar sinais de interrupção
wait
