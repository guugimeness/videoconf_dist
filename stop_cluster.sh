#!/bin/bash
# STOP CLUSTER: Para todos os brokers e clientes

echo "🛑 Parando cluster de brokers..."
echo ""

# Parar todos os brokers
echo "Parando brokers..."
pkill -f broker_node
sleep 1

# Parar todos os clientes
echo "Parando clientes..."
pkill -f client.py
sleep 1

# Verificar se ainda há processos
echo "Verificando processos restantes..."
REMAINING=$(ps aux | grep -E "(broker_node|client\.py)" | grep -v grep | wc -l)

if [ $REMAINING -eq 0 ]; then
    echo "✅ Todos os processos foram encerrados!"
else
    echo "⚠️  Ainda há $REMAINING processos ativos."
    echo "Para forçar encerramento:"
    echo "  pkill -9 -f broker_node"
    echo "  pkill -9 -f client.py"
fi

echo ""
echo "Cluster parado com sucesso!"