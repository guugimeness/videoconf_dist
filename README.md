# videoconf_dist

Sistema de videoconferência assíncrona.

# Build
docker build -t teste_pyzmq .

# Subir Broker
docker-compose up broker

# Subir Client 1
docker run -it --rm \--network host \-v $(pwd):/app \teste_pyzmq \python src/client/client_text.py user1 SALA_A

# Subir Client 1
docker run -it --rm \--network host \-v $(pwd):/app \teste_pyzmq \python src/client/client_text.py user2 SALA_A

# Para excluir o container do broker
docker-compose down