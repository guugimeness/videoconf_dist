"""
Broker Discovery Module for Cluster Mode

This module provides functions to discover and select brokers for clients.
<<<<<<< HEAD
Supports both single-broker and cluster modes with dynamic discovery.
=======
Supports both single-broker and cluster modes.
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
"""

import hashlib
import random
<<<<<<< HEAD
import socket
import threading
import time
import json
=======
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
from typing import Dict, List, Optional
from . import config


<<<<<<< HEAD
class RegistryClient:
    """Client for centralized broker registry service."""

    def __init__(self, registry_host: str = None, registry_port: int = None):
        self.registry_host = registry_host or config.REGISTRY_HOST
        self.registry_port = registry_port or config.REGISTRY_PORT
        self._brokers_cache = []
        self._last_update = 0
        self._cache_timeout = 30  # Cache for 30 seconds

    def register_broker(self, broker_info: Dict) -> bool:
        """Register a broker with the central registry."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect((self.registry_host, self.registry_port))

                request = {
                    "action": "register",
                    "broker": broker_info,
                    "timestamp": time.time()
                }

                sock.send(json.dumps(request).encode())
                response = sock.recv(1024).decode()

                return json.loads(response).get("status") == "ok"
        except Exception as e:
            print(f"Registry registration failed: {e}")
            return False

    def unregister_broker(self, broker_id: int) -> bool:
        """Unregister a broker from the central registry."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect((self.registry_host, self.registry_port))

                request = {
                    "action": "unregister",
                    "broker_id": broker_id,
                    "timestamp": time.time()
                }

                sock.send(json.dumps(request).encode())
                response = sock.recv(1024).decode()

                return json.loads(response).get("status") == "ok"
        except Exception as e:
            print(f"Registry unregistration failed: {e}")
            return False

    def get_all_brokers(self) -> List[Dict]:
        """Get list of all registered brokers from registry."""
        # Use cache if recent
        if time.time() - self._last_update < self._cache_timeout and self._brokers_cache:
            return self._brokers_cache.copy()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect((self.registry_host, self.registry_port))

                request = {
                    "action": "get_brokers",
                    "timestamp": time.time()
                }

                sock.send(json.dumps(request).encode())
                response = sock.recv(4096).decode()
                data = json.loads(response)

                if data.get("status") == "ok":
                    self._brokers_cache = data.get("brokers", [])
                    self._last_update = time.time()
                    return self._brokers_cache.copy()

        except Exception as e:
            print(f"Failed to get brokers from registry: {e}")

        # Fallback to static config
        return config.BROKER_LIST.copy()

    def heartbeat(self, broker_id: int) -> bool:
        """Send heartbeat to registry to indicate broker is alive."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect((self.registry_host, self.registry_port))

                request = {
                    "action": "heartbeat",
                    "broker_id": broker_id,
                    "timestamp": time.time()
                }

                sock.send(json.dumps(request).encode())
                response = sock.recv(1024).decode()

                return json.loads(response).get("status") == "ok"
        except Exception as e:
            print(f"Registry heartbeat failed: {e}")
            return False


class UDPDiscovery:
    """UDP broadcast discovery for brokers in local network."""

    def __init__(self, broadcast_port: int = None):
        self.broadcast_port = broadcast_port or config.UDP_BROADCAST_PORT
        self._discovered_brokers = {}
        self._running = False
        self._listener_thread = None

    def start_broadcasting(self, broker_info: Dict):
        """Start broadcasting broker presence via UDP."""
        def broadcast_worker():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            message = json.dumps({
                "type": "broker_announce",
                "broker": broker_info,
                "timestamp": time.time()
            }).encode()

            broadcast_addr = ('255.255.255.255', self.broadcast_port)

            while self._running:
                try:
                    sock.sendto(message, broadcast_addr)
                    time.sleep(config.UDP_BROADCAST_INTERVAL)
                except Exception as e:
                    print(f"UDP broadcast failed: {e}")
                    time.sleep(5)

            sock.close()

        self._running = True
        self._broadcast_thread = threading.Thread(target=broadcast_worker, daemon=True)
        self._broadcast_thread.start()

    def start_listening(self):
        """Start listening for UDP broadcasts from other brokers."""
        def listen_worker():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.broadcast_port))

            while self._running:
                try:
                    data, addr = sock.recvfrom(4096)
                    message = json.loads(data.decode())

                    if message.get("type") == "broker_announce":
                        broker = message["broker"]
                        broker_id = broker["broker_id"]
                        self._discovered_brokers[broker_id] = {
                            **broker,
                            "last_seen": time.time(),
                            "source_ip": addr[0]
                        }

                except Exception as e:
                    print(f"UDP listen failed: {e}")
                    time.sleep(1)

            sock.close()

        self._running = True
        self._listener_thread = threading.Thread(target=listen_worker, daemon=True)
        self._listener_thread.start()

    def stop(self):
        """Stop UDP discovery."""
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=2)
        if hasattr(self, '_broadcast_thread'):
            self._broadcast_thread.join(timeout=2)

    def get_discovered_brokers(self) -> List[Dict]:
        """Get list of brokers discovered via UDP broadcast."""
        # Clean up old entries (older than 2x broadcast interval)
        cutoff = time.time() - (config.UDP_BROADCAST_INTERVAL * 2)
        self._discovered_brokers = {
            k: v for k, v in self._discovered_brokers.items()
            if v["last_seen"] > cutoff
        }

        return list(self._discovered_brokers.values())


# Global instances
_registry_client = None
_udp_discovery = None


def get_registry_client() -> RegistryClient:
    """Get or create registry client instance."""
    global _registry_client
    if _registry_client is None:
        _registry_client = RegistryClient()
    return _registry_client


def get_udp_discovery() -> UDPDiscovery:
    """Get or create UDP discovery instance."""
    global _udp_discovery
    if _udp_discovery is None:
        _udp_discovery = UDPDiscovery()
    return _udp_discovery


def is_dynamic_discovery_enabled() -> bool:
    """Check if dynamic discovery is enabled."""
    return config.SERVICE_DISCOVERY_MODE in ["registry", "broadcast", "hybrid"]


def get_broker_for_user(username: str) -> Dict:
    """
    Calculate which broker a user should connect to.

    Uses consistent hashing: broker_index = hash(username) % len(BROKER_LIST)
    This ensures the same user always goes to the same broker (for reconnection).

    Args:
        username: The username to hash

    Returns:
        Dict with broker info (host, ports, broker_id)

=======
def get_broker_for_user(username: str) -> Dict:
    """
    Calculate which broker a user should connect to.
    
    Uses consistent hashing: broker_index = hash(username) % len(BROKER_LIST)
    This ensures the same user always goes to the same broker (for reconnection).
    
    Args:
        username: The username to hash
        
    Returns:
        Dict with broker info (host, ports, broker_id)
        
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
    Example:
        >>> broker = get_broker_for_user("alice")
        >>> connect(broker["host"], broker["publish_port"])
    """
<<<<<<< HEAD
    brokers = get_all_brokers()
    if not brokers:
        raise ValueError("No brokers available")

    # Consistent hashing: same user always maps to same broker
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    broker_index = hash_value % len(brokers)

    return brokers[broker_index]
=======
    if not config.BROKER_LIST:
        raise ValueError("BROKER_LIST is empty in config")
    
    # Consistent hashing: same user always maps to same broker
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    broker_index = hash_value % len(config.BROKER_LIST)
    
    return config.BROKER_LIST[broker_index]
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8


def get_all_brokers() -> List[Dict]:
    """
    Get list of all brokers in the cluster.
<<<<<<< HEAD

    Uses dynamic discovery if enabled, falls back to static config.
    """
    if config.SERVICE_DISCOVERY_MODE == "registry":
        return get_registry_client().get_all_brokers()
    elif config.SERVICE_DISCOVERY_MODE == "broadcast":
        discovered = get_udp_discovery().get_discovered_brokers()
        return discovered if discovered else config.BROKER_LIST
    elif config.SERVICE_DISCOVERY_MODE == "hybrid":
        # Try registry first, then UDP, then static
        brokers = get_registry_client().get_all_brokers()
        if not brokers:
            brokers = get_udp_discovery().get_discovered_brokers()
        return brokers if brokers else config.BROKER_LIST
    else:
        # Static mode
        return config.BROKER_LIST
=======
    
    Returns:
        List of broker info dicts
    """
    return config.BROKER_LIST
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8


def get_broker_by_id(broker_id: int) -> Optional[Dict]:
    """
    Get broker info by its ID.
<<<<<<< HEAD

    Uses the static BROKER_LIST for broker self-identification, because
    broker startup must find its own config before dynamic discovery is active.

    Args:
        broker_id: The broker ID

=======
    
    Args:
        broker_id: The broker ID
        
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
    Returns:
        Broker info dict or None if not found
    """
    for broker in config.BROKER_LIST:
        if broker["broker_id"] == broker_id:
            return broker
    return None


def select_fallback_broker(primary_broker: Dict, username: str) -> Optional[Dict]:
    """
    Select a fallback broker if primary broker fails.
    
    Returns a random broker from the cluster (excluding primary).
    Used for automatic failover.
    
    Args:
        primary_broker: The primary broker that failed
        username: Username (for future weighted selection)
        
    Returns:
        A different broker dict, or None if only 1 broker exists
    """
<<<<<<< HEAD
    brokers = get_all_brokers()
    if len(brokers) <= 1:
        return None
    
    fallback = [b for b in brokers if b["broker_id"] != primary_broker["broker_id"]]
=======
    if len(config.BROKER_LIST) <= 1:
        return None
    
    fallback = [b for b in config.BROKER_LIST if b["broker_id"] != primary_broker["broker_id"]]
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
    return random.choice(fallback) if fallback else None


def select_broker_round_robin() -> Dict:
    """
    Select a broker using round-robin (for load balancing without username).
    
    Useful for initial connection before username is known.
    
    Returns:
        Broker info dict
    """
<<<<<<< HEAD
    brokers = get_all_brokers()
    return random.choice(brokers)
=======
    return random.choice(config.BROKER_LIST)
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8


def get_connection_string(broker: Dict, socket_type: str = "publish") -> str:
    """
    Build ZeroMQ connection string for a broker.
    
    Args:
        broker: Broker info dict
        socket_type: "publish" (XSUB), "subscribe" (XPUB), "auth" (REP), 
                     "broker_pub", or "broker_sub"
    
    Returns:
        Connection string like "tcp://host:port"
    """
    port_map = {
        "publish": broker["publish_port"],
        "subscribe": broker["subscribe_port"],
        "auth": broker["auth_port"],
        "broker_pub": broker.get("broker_pub_port"),
        "broker_sub": broker.get("broker_sub_port"),
    }
    
    port = port_map.get(socket_type)
    if port is None:
        raise ValueError(f"Unknown socket_type: {socket_type}")
    
    return f"tcp://{broker['host']}:{port}"


def is_cluster_mode() -> bool:
    """Check if cluster mode is enabled."""
    return config.BROKER_CLUSTER_MODE and len(config.BROKER_LIST) > 1


def get_num_brokers() -> int:
    """Get total number of brokers in the cluster."""
    return len(config.BROKER_LIST)


def validate_broker_config() -> bool:
    """
    Validate broker configuration.
    
    Checks:
    - BROKER_LIST is not empty
    - All brokers have required fields
    - Broker IDs are unique
    
    Returns:
        True if valid, raises ValueError otherwise
    """
    if not config.BROKER_LIST:
        raise ValueError("BROKER_LIST is empty")
    
    broker_ids = set()
    required_fields = ["broker_id", "host", "publish_port", "subscribe_port", "auth_port"]
    
    for broker in config.BROKER_LIST:
        # Check required fields
        for field in required_fields:
            if field not in broker:
                raise ValueError(f"Broker missing required field: {field}")
        
        # Check unique broker IDs
        broker_id = broker["broker_id"]
        if broker_id in broker_ids:
            raise ValueError(f"Duplicate broker_id: {broker_id}")
        broker_ids.add(broker_id)
    
    return True


if __name__ == "__main__":
    # Test the module
    print("Testing broker_discovery module...")
    
    # Test get_broker_for_user
    broker_alice = get_broker_for_user("alice")
    broker_bob = get_broker_for_user("bob")
    print(f"Alice goes to broker {broker_alice['broker_id']}")
    print(f"Bob goes to broker {broker_bob['broker_id']}")
    
    # Test consistency
    broker_alice_2 = get_broker_for_user("alice")
    assert broker_alice["broker_id"] == broker_alice_2["broker_id"], "Consistency check failed"
    print("✓ Consistency check passed")
    
    # Test get_all_brokers
    all_brokers = get_all_brokers()
    print(f"✓ Total brokers: {len(all_brokers)}")
    
    # Test validate_broker_config
    try:
        validate_broker_config()
        print("✓ Broker config is valid")
    except ValueError as e:
        print(f"✗ Config error: {e}")
    
    print("\nAll tests passed!")
