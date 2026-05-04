"""
Broker Discovery Module for Cluster Mode

This module provides functions to discover and select brokers for clients.
Supports both single-broker and cluster modes.
"""

import hashlib
import random
from typing import Dict, List, Optional
from . import config


def get_broker_for_user(username: str) -> Dict:
    """
    Calculate which broker a user should connect to.
    
    Uses consistent hashing: broker_index = hash(username) % len(BROKER_LIST)
    This ensures the same user always goes to the same broker (for reconnection).
    
    Args:
        username: The username to hash
        
    Returns:
        Dict with broker info (host, ports, broker_id)
        
    Example:
        >>> broker = get_broker_for_user("alice")
        >>> connect(broker["host"], broker["publish_port"])
    """
    if not config.BROKER_LIST:
        raise ValueError("BROKER_LIST is empty in config")
    
    # Consistent hashing: same user always maps to same broker
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    broker_index = hash_value % len(config.BROKER_LIST)
    
    return config.BROKER_LIST[broker_index]


def get_all_brokers() -> List[Dict]:
    """
    Get list of all brokers in the cluster.
    
    Returns:
        List of broker info dicts
    """
    return config.BROKER_LIST


def get_broker_by_id(broker_id: int) -> Optional[Dict]:
    """
    Get broker info by its ID.
    
    Args:
        broker_id: The broker ID
        
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
    if len(config.BROKER_LIST) <= 1:
        return None
    
    fallback = [b for b in config.BROKER_LIST if b["broker_id"] != primary_broker["broker_id"]]
    return random.choice(fallback) if fallback else None


def select_broker_round_robin() -> Dict:
    """
    Select a broker using round-robin (for load balancing without username).
    
    Useful for initial connection before username is known.
    
    Returns:
        Broker info dict
    """
    return random.choice(config.BROKER_LIST)


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
