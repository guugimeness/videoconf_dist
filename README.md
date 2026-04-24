# Ferramenta de Videoconferência

Sistema de videoconferência assíncrona.

### Build da Imagem

```bash
docker build -t videoconf .
```

### Iniciar o Broker

```bash
docker-compose up broker
```

### Iniciar Clientes de Áudio

Em terminais diferentes:

```bash
# Terminal 2: Usuário 1
docker run -it --rm \
  --network host \
  -v $(pwd):/app \
  videoconf \
  python src/client/client_audio.py user1 SALA_A

# Terminal 3: Usuário 2
docker run -it --rm \
  --network host \
  -v $(pwd):/app \
  videoconf \
  python src/client/client_audio.py user2 SALA_A
```


### Iniciar Clientes de Texto

**Exemplo:**
```bash
# Terminal 1
docker run -it --rm --network host -v $(pwd):/app \teste_pyzmq \python src/client/client_text.py user1 SALA_A

# Terminal 2
docker run -it --rm --network host -v $(pwd):/app \teste_pyzmq \python src/client/client_text.py user2 SALA_A
```

**Interação:**
```
Bem-vindo(a) alice à SALA_A!
Digite sua mensagem e aperte Enter (Ctrl+C para sair):
> Olá pessoal!

[bob]: Oi Alice! Tudo bem?
> 
```
