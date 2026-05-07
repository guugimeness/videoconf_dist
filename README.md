# Ferramenta de Videoconferência

Sistema de videoconferência assíncrona com **descoberta dinâmica de serviços**.

## 🚀 Novos Recursos

### Descoberta Dinâmica de Brokers
- ✅ **Registry Centralizado**: Brokers se registram automaticamente
- ✅ **Broadcast UDP**: Descoberta automática na rede local
- ✅ **Tolerância a Falhas**: Detecção automática de brokers inativos
- ✅ **Modo Híbrido**: Combina registry + UDP para máxima confiabilidade

### Build da Imagem

```bash
docker build -t videoconf .
```

### Iniciar o Sistema

Inicie o registry e os brokers manualmente conforme descrito abaixo.

### Iniciar Manualmente

**1. Iniciar Registry:**
```bash
PYTHONPATH=src python3 -m src.broker.registry_server
```

**2. Iniciar Brokers:**
```bash
# Terminal 1
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 0

# Terminal 2
PYTHONPATH=src python3 src/broker/broker_node.py --broker-id 1
```

### Iniciar Clientes

Em terminais diferentes:

```bash
# Usuário 1 (conecta automaticamente ao broker correto)
PYTHONPATH=src python3 src/client/client.py user1 SALA_A

# Usuário 2 (conecta automaticamente ao broker correto)
PYTHONPATH=src python3 src/client/client.py user2 SALA_A
```

### Fechar o Sistema

```bash
# No launcher: Ctrl+C para shutdown graceful
# Ou manualmente: Ctrl+C em cada terminal
```

## 📋 Status dos Requisitos

| Requisito | Status | Implementação |
|-----------|--------|---|
| 1. Arquitetura Distribuída | ✅ Completo | `broker_node.py` |
| 2. **Descoberta de Serviços** | ✅ **Completo** | `broker_discovery.py` + Registry |
| 3. Tolerância a Falhas | ✅ Completo | Heartbeats + Fallback |
| 4. QoS Simplificado | ✅ Completo | Clients especializados |
| 5. Concorrência | ✅ Completo | Threads em todos os clients |
| 6. Identidade e Sessão | ✅ Completo | Registry global |

**Sistema pronto para produção com descoberta dinâmica! 🎉**