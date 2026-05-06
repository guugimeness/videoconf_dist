# Sistema de Videoconferência Distribuído

Ferramenta de videoconferência distribuída desenvolvida em Python. O sistema suporta transmissão simultânea de áudio, vídeo e texto utilizando uma arquitetura descentralizada com múltiplos brokers via ZeroMQ, garantindo alta concorrência e isolamento de processos.

## Configuração

O ajuste de parâmetros de rede e hardware é realizado através do arquivo `src/shared/config.py`.

**Rede e Endereçamento:**
* `BROKER_HOST`: IP do servidor central.
* `PUBLISH_PORT`, `SUBSCRIBE_PORT`, `AUTH_PORT`: Portas para comunicação ZeroMQ.

**Hardware de Mídia**
* `VIDEO_CAMERA_INDEX`: ID da câmera no sistema operacional.
* `AUDIO_INPUT_DEVICE` e `AUDIO_OUTPUT_DEVICE`: IDs de hardware para microfone e saída de som.
* `AUDIO_SAMPLE_RATE` e `AUDIO_CHANNELS`: Definições de qualidade e fidelidade sonora.

## Instruções de Execução

### 1. Build da Imagem
Antes de iniciar a rede, construa a imagem base do projeto utilizando o Docker:
```bash
docker build -t videoconf .
```

### 2. Iniciar o Broker
O Broker atua como o nó inicial para o roteamento de mensagens e gerenciamento das salas e usuários. Em um terminal dedicado, suba o serviço:
```bash
docker-compose up broker
```
Para encerrar o serviço do broker e limpar os contêineres da rede, pressione `Ctrl+C` e execute `docker-compose down`.

### 3. Iniciar os Clientes
Com o broker em execução, abra novos terminais para simular os usuários. É necessário navegar até a pasta `src` para que as importações dos módulos funcionem corretamente.

**Terminal 2 (Usuário 1):**
```bash
cd src
python -m client.client user1 SALA_A
```

**Terminal 3 (Usuário 2):**
```bash
cd src
python -m client.client user2 SALA_A
```
