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

# List of brokers in cluster
# Each broker has: host, PUBLISH_PORT (XSUB), SUBSCRIBE_PORT (XPUB), AUTH_PORT (REP), BROKER_ID
BROKER_LIST = [
    {
        "broker_id": 0,
        "host": "127.0.0.1",
        "publish_port": 6555,    # XSUB port
        "subscribe_port": 6556,  # XPUB port
        "auth_port": 6557,       # REP port
        "broker_pub_port": 6560, # PUB port for inter-broker communication
        "broker_sub_port": 6561, # SUB port for inter-broker communication
    },
    {
        "broker_id": 1,
        "host": "127.0.0.1",
        "publish_port": 6565,    # XSUB port
        "subscribe_port": 6566,  # XPUB port
        "auth_port": 6567,       # REP port
        "broker_pub_port": 6570, # PUB port for inter-broker communication
        "broker_sub_port": 6571, # SUB port for inter-broker communication
    },
    {
        "broker_id": 2,
        "host": "127.0.0.1",
        "publish_port": 6575,    # XSUB port
        "subscribe_port": 6576,  # XPUB port
        "auth_port": 6577,       # REP port
        "broker_pub_port": 6580, # PUB port for inter-broker communication
        "broker_sub_port": 6581, # SUB port for inter-broker communication
    },
]

VIDEO_CAMERA_INDEX = 0

# Params Audio
AUDIO_INPUT_DEVICE = 0
AUDIO_OUTPUT_DEVICE = 6
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 1
