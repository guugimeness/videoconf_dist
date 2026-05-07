# ============================================================================
# BROKER CONFIGURATION - Single Broker (Legacy) or Cluster Mode
# ============================================================================

# Legacy single-broker mode (backward compatibility)
BROKER_HOST = "192.168.18.18"
PUBLISH_PORT = 5555
SUBSCRIBE_PORT = 5556
AUTH_PORT = 5557

# Cluster mode: multiple brokers cooperating
BROKER_CLUSTER_MODE = True  # Set to True to enable cluster mode

<<<<<<< HEAD
# Dynamic Service Discovery Configuration
SERVICE_DISCOVERY_MODE = "broadcast"  # Options: "static", "registry", "broadcast", "hybrid"
ENABLE_UDP_BROADCAST = True  # Enable UDP broadcast discovery
UDP_BROADCAST_PORT = 9999  # Port for UDP broadcast discovery
UDP_BROADCAST_INTERVAL = 30  # Seconds between broadcasts

# Registry Configuration (for centralized discovery)
REGISTRY_HOST = "192.168.18.18"  # Host where registry runs (usually broker 0)
REGISTRY_PORT = 8888  # TCP port for registry service
REGISTRY_HEARTBEAT_INTERVAL = 60  # Seconds between heartbeats to registry
REGISTRY_TIMEOUT = 180  # Seconds before considering broker dead

# List of brokers in cluster (fallback for static mode)
=======
# List of brokers in cluster
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
# Each broker has: host, PUBLISH_PORT (XSUB), SUBSCRIBE_PORT (XPUB), AUTH_PORT (REP), BROKER_ID
BROKER_LIST = [
    {
        "broker_id": 0,
<<<<<<< HEAD
        "host": "192.168.18.18",
=======
        "host": "127.0.0.1",
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
        "publish_port": 6555,    # XSUB port
        "subscribe_port": 6556,  # XPUB port
        "auth_port": 6557,       # REP port
        "broker_pub_port": 6560, # PUB port for inter-broker communication
        "broker_sub_port": 6561, # SUB port for inter-broker communication
    },
    {
        "broker_id": 1,
<<<<<<< HEAD
        "host": "192.168.18.200",
=======
        "host": "127.0.0.1",
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
        "publish_port": 6565,    # XSUB port
        "subscribe_port": 6566,  # XPUB port
        "auth_port": 6567,       # REP port
        "broker_pub_port": 6570, # PUB port for inter-broker communication
        "broker_sub_port": 6571, # SUB port for inter-broker communication
    },
<<<<<<< HEAD
=======
    {
        "broker_id": 2,
        "host": "127.0.0.1",
        "publish_port": 6575,    # XSUB port
        "subscribe_port": 6576,  # XPUB port
        "auth_port": 6577,       # REP port
        "broker_pub_port": 6580, # PUB port for inter-broker communication
        "broker_sub_port": 6581, # SUB port for inter-broker communication
    },
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
]

VIDEO_CAMERA_INDEX = 0

# Params Audio
AUDIO_INPUT_DEVICE = 0
AUDIO_OUTPUT_DEVICE = 6
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 1
