"""
Broker Node - Cluster-aware message broker with inter-broker communication.

This broker can operate in two modes:
1. Legacy mode: Single broker (backward compatible with broker_central.py)
2. Cluster mode: Multiple brokers with PUB/SUB inter-broker communication

Features:
- XSUB/XPUB multiplexing for client connections
- REP socket for authentication (LOGIN)
- Global PUB/SUB for inter-broker communication
- Distributed user management (each broker manages a subset)
- Session timeout detection
- Global duplicate prevention (same username cannot exist across brokers)

Usage:
    # Single broker (legacy)
    python broker_node.py --broker-id 0
    
    # Cluster: start multiple brokers with different IDs
    python broker_node.py --broker-id 0 &
    python broker_node.py --broker-id 1 &
    python broker_node.py --broker-id 2 &
"""

import zmq
import time
import argparse
import sys
import json
import hashlib
<<<<<<< HEAD
import threading
=======
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import config
from shared import broker_discovery


# Session timeout in seconds
SESSION_TIMEOUT = 30


class BrokerNode:
    """A broker node that can operate in cluster mode."""
    
    def __init__(self, broker_id: int):
        """
        Initialize a broker node.
        
        Args:
            broker_id: Unique ID for this broker in the cluster
        """
        # Get broker configuration
        broker_config = broker_discovery.get_broker_by_id(broker_id)
        if not broker_config is None:
            self.broker_config = broker_config
        else:
            raise ValueError(f"Broker ID {broker_id} not found in config")
        
        self.broker_id = broker_id
        self.context = zmq.Context()
        
        # Cluster info
        self.is_cluster = broker_discovery.is_cluster_mode()
        self.num_brokers = broker_discovery.get_num_brokers()
        
        # User management
        self.active_users = {}  # Users connected to THIS broker
        self.known_users_global = {}  # Users known in the entire cluster
        
        # Message forwarding cache to prevent loops
        self.forwarded_messages = set()  # Set of recently forwarded message IDs
        
        self.msg_count = 0
<<<<<<< HEAD
        self.poller = None
        
        # Dynamic discovery
        self._discovery_enabled = broker_discovery.is_dynamic_discovery_enabled()
        self._registry_client = None
        self._udp_discovery = None
        self._heartbeat_thread = None
        self._last_heartbeat = 0
        
        print(f"[BROKER-{self.broker_id}] Initializing broker node...")
        print(f"[BROKER-{self.broker_id}] Cluster mode: {self.is_cluster}")
        print(f"[BROKER-{self.broker_id}] Dynamic discovery: {self._discovery_enabled}")
        print(f"[BROKER-{self.broker_id}] Total brokers: {self.num_brokers}")
        
        self._setup_sockets()
        self._setup_dynamic_discovery()
=======
        self.relay_print_count = 0
        self.poller = None
        
        print(f"[BROKER-{self.broker_id}] Initializing broker node...")
        print(f"[BROKER-{self.broker_id}] Cluster mode: {self.is_cluster}")
        print(f"[BROKER-{self.broker_id}] Total brokers: {self.num_brokers}")
        
        self._setup_sockets()
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
    
    def _setup_sockets(self):
        """Setup all ZeroMQ sockets."""
        # Client-facing sockets
        self.frontend = self.context.socket(zmq.XSUB)
        self.frontend.setsockopt(zmq.RCVHWM, 100)
        self.frontend.bind(broker_discovery.get_connection_string(
            self.broker_config, "publish"
        ))
        
        self.backend = self.context.socket(zmq.XPUB)
        self.backend.setsockopt(zmq.SNDHWM, 100)
        self.backend.bind(broker_discovery.get_connection_string(
            self.broker_config, "subscribe"
        ))
        
        self.auth_socket = self.context.socket(zmq.REP)
        self.auth_socket.bind(broker_discovery.get_connection_string(
            self.broker_config, "auth"
        ))
        
        print(f"[BROKER-{self.broker_id}] Client sockets bound:")
        print(f"  - XSUB (publish): {broker_discovery.get_connection_string(self.broker_config, 'publish')}")
        print(f"  - XPUB (subscribe): {broker_discovery.get_connection_string(self.broker_config, 'subscribe')}")
        print(f"  - REP (auth): {broker_discovery.get_connection_string(self.broker_config, 'auth')}")
        
        # Inter-broker communication (only in cluster mode)
        if self.is_cluster:
            self.broker_pub = self.context.socket(zmq.PUB)
            self.broker_pub.bind(broker_discovery.get_connection_string(
                self.broker_config, "broker_pub"
            ))
            
            self.broker_sub = self.context.socket(zmq.SUB)
            self.broker_sub.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all topics
            
            # Connect to all other brokers' PUB sockets
            for broker in broker_discovery.get_all_brokers():
                if broker["broker_id"] != self.broker_id:
                    conn_str = broker_discovery.get_connection_string(broker, "broker_pub")
                    self.broker_sub.connect(conn_str)
                    print(f"[BROKER-{self.broker_id}] Connected to broker {broker['broker_id']}: {conn_str}")
            
            print(f"[BROKER-{self.broker_id}] Inter-broker sockets ready")
        else:
            self.broker_pub = None
            self.broker_sub = None
        
        # Setup poller
        self.poller = zmq.Poller()
        self.poller.register(self.frontend, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)
        self.poller.register(self.auth_socket, zmq.POLLIN)
        
        if self.is_cluster:
            self.poller.register(self.broker_sub, zmq.POLLIN)
    
<<<<<<< HEAD
    def _setup_dynamic_discovery(self):
        """Setup dynamic service discovery."""
        if not self._discovery_enabled:
            return
        
        print(f"[BROKER-{self.broker_id}] Setting up dynamic discovery...")
        
        # Registry-based discovery
        if config.SERVICE_DISCOVERY_MODE in ["registry", "hybrid"]:
            self._registry_client = broker_discovery.get_registry_client()
            
            # Register this broker
            success = self._registry_client.register_broker(self.broker_config)
            if success:
                print(f"[BROKER-{self.broker_id}] ✓ Registered with registry")
                
                # Start heartbeat thread
                self._start_heartbeat_thread()
            else:
                print(f"[BROKER-{self.broker_id}] ✗ Failed to register with registry")
        
        # UDP broadcast discovery
        if config.SERVICE_DISCOVERY_MODE in ["broadcast", "hybrid"] and config.ENABLE_UDP_BROADCAST:
            self._udp_discovery = broker_discovery.get_udp_discovery()
            
            # Start broadcasting presence
            self._udp_discovery.start_broadcasting(self.broker_config)
            
            # Start listening for other brokers
            self._udp_discovery.start_listening()
            
            print(f"[BROKER-{self.broker_id}] ✓ UDP broadcast discovery started")
    
    def _start_heartbeat_thread(self):
        """Start background thread for registry heartbeats."""
        def heartbeat_worker():
            while self._registry_client:
                try:
                    time.sleep(config.REGISTRY_HEARTBEAT_INTERVAL)
                    success = self._registry_client.heartbeat(self.broker_id)
                    if success:
                        print(f"[BROKER-{self.broker_id}] ✓ Registry heartbeat sent")
                    else:
                        print(f"[BROKER-{self.broker_id}] ✗ Registry heartbeat failed")
                except Exception as e:
                    print(f"[BROKER-{self.broker_id}] Heartbeat error: {e}")
                    time.sleep(5)  # Retry sooner on error
        
        self._heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        self._heartbeat_thread.start()
        print(f"[BROKER-{self.broker_id}] ✓ Heartbeat thread started")
    
=======
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
    def _broadcast_login_event(self, username: str, room: str):
        """
        Broadcast login event to all brokers.
        
        Format: BROKER:<broker_id>:LOGIN|<username>|<room>
        """
        if not self.is_cluster:
            return
        
        event = f"BROKER:{self.broker_id}:LOGIN|{username}|{room}".encode('utf-8')
        self.broker_pub.send(event)
    
    def _broadcast_logout_event(self, username: str):
        """
        Broadcast logout event to all brokers.
        
        Format: BROKER:<broker_id>:LOGOUT|<username>
        """
        if not self.is_cluster:
            return
        
        event = f"BROKER:{self.broker_id}:LOGOUT|{username}".encode('utf-8')
        self.broker_pub.send(event)
    
    def _broadcast_heartbeat_event(self, username: str):
        """
        Broadcast heartbeat event to keep user alive in global registry.
        
        Format: BROKER:<broker_id>:HEARTBEAT|<username>
        """
        if not self.is_cluster:
            return
        
        event = f"BROKER:{self.broker_id}:HEARTBEAT|{username}".encode('utf-8')
        self.broker_pub.send(event)
    
    def _handle_broker_event(self, event_bytes: bytes):
        """
        Handle event from another broker.
        
        Updates known_users_global and removes users on LOGOUT events.
        Also handles forwarded messages from other brokers.
        """
        try:
            event_str = event_bytes.decode('utf-8', errors='ignore')
            
            if event_str.startswith("MESSAGE:"):
                # Handle forwarded message: "MESSAGE:origin_broker:msg_id|original_message"
                parts = event_str.split("|", 2)
                if len(parts) >= 2:
                    header = parts[0]  # "MESSAGE:origin_broker:msg_id"
<<<<<<< HEAD
                    original_msg = parts[1]
=======
                    original_msg = "|".join(parts[1:])
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
                    
                    header_parts = header.split(":")
                    if len(header_parts) >= 3:
                        origin_broker = int(header_parts[1])
                        msg_id = header_parts[2]
                        
                        # Prevent loops: don't process messages from this broker or already forwarded
                        if origin_broker != self.broker_id and msg_id not in self.forwarded_messages:
                            # Relay the original message to local subscribers
                            self.backend.send(original_msg.encode('utf-8'))
<<<<<<< HEAD
                            print(f"[BROKER-{self.broker_id}] Relayed forwarded message {msg_id} from broker {origin_broker}")
=======
                            
                            self.relay_print_count += 1
                            
                            #print(f"[BROKER-{self.broker_id}] Relayed forwarded message {msg_id} from broker {origin_broker}")
                            
                            if self.relay_print_count % 20 == 0:
                                print(
                                    f"[BROKER-{self.broker_id}] "
                                    f"Relayed {self.relay_print_count} messages "
                                    f"from broker {origin_broker}"
                                )
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
                            return
            
            # Handle other events (LOGIN, LOGOUT, HEARTBEAT)
            parts = event_str.split("|", 3)
            
            if len(parts) < 2:
                return
            
            broker_msg = parts[0]  # Format: "BROKER:X:EVENT"
            event_parts = broker_msg.split(":")
            
            if len(event_parts) < 3:
                return
            
            event_type = event_parts[2]  # LOGIN, LOGOUT, HEARTBEAT
            
            if event_type == "LOGIN" and len(parts) >= 3:
                username = parts[1]
                room = parts[2]
                self.known_users_global[username] = {
                    "room": room,
                    "last_seen": time.time()
                }
                print(f"[BROKER-{self.broker_id}] Global: User '{username}' logged in (room: {room})")
            
            elif event_type == "LOGOUT" and len(parts) >= 2:
                username = parts[1]
                if username in self.known_users_global:
                    del self.known_users_global[username]
                print(f"[BROKER-{self.broker_id}] Global: User '{username}' logged out")
            
            elif event_type == "HEARTBEAT" and len(parts) >= 2:
                username = parts[1]
                if username in self.known_users_global:
                    self.known_users_global[username]["last_seen"] = time.time()
        
        except Exception as e:
            print(f"[BROKER-{self.broker_id}] Error handling broker event: {e}")
    
    def _handle_login(self, request: str) -> str:
        """
        Handle LOGIN request from client.
        
        Format: "LOGIN|<room>|<username>"
        
        Returns:
            "OK" if login successful, error message otherwise
        """
        try:
            parts = request.split("|")
            if len(parts) < 3:
                return "ERRO: Formato inválido"
            
            acao, sala, usuario = parts[0], parts[1], parts[2]
            
            if acao != "LOGIN":
                return "ERRO: Ação inválida"
            
            # Check if user already exists locally
            if usuario in self.active_users:
                return "ERRO: Você já está conectado a este broker"
            
            # Check if user exists globally (in cluster mode)
            if self.is_cluster and usuario in self.known_users_global:
<<<<<<< HEAD
                return "ERRO: Nome já está em uso (conectado em outro broker)"
=======
               print(f"[BROKER-{self.broker_id}] Reclaiming global session for {usuario}")
               self.known_users_global.pop(usuario, None)
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
            
            # Register user locally
            self.active_users[usuario] = {
                "room": sala,
                "last_seen": time.time()
            }
            
            # Register globally (in cluster mode)
            self.known_users_global[usuario] = {
                "room": sala,
                "last_seen": time.time()
            }
            
            print(f"[BROKER-{self.broker_id}] '{usuario}' logged in (room: {sala})")
            
            # Broadcast login event
            self._broadcast_login_event(usuario, sala)
            
            # Inject system message
            aviso = f"{sala}:TEXTO:SISTEMA:0|O usuário '{usuario}' entrou na sala."
            self.backend.send(aviso.encode('utf-8'))
            
            return "OK"
        
        except Exception as e:
            return f"ERRO: {str(e)}"
    
    def _extract_room_from_message(self, parts):
        """Extract room name from message parts."""
        try:
            if len(parts) == 1:
                # Text/Audio format: "SALA:TIPO:NOME:ID|payload"
                header = parts[0].decode('utf-8', errors='ignore').split("|")[0]
                return header.split(":")[0]
            elif len(parts) == 5:
                # Video format: [room, sender, msg_id, timestamp, payload]
                return parts[0].decode('utf-8', errors='ignore')
        except:
            pass
        return None
    
    def _get_brokers_with_room_users(self, room):
        """Return list of broker_ids that have users in the given room."""
        brokers = set()
        for username, info in self.known_users_global.items():
            if info["room"] == room:
                # Calculate which broker the user should be on
                user_broker = broker_discovery.get_broker_for_user(username)["broker_id"]
                brokers.add(user_broker)
        return list(brokers)
    
    def _generate_message_id(self, parts):
        """Generate unique ID for the message to prevent loops."""
        msg_bytes = b"".join(parts) if isinstance(parts[0], bytes) else str(parts).encode()
        return hashlib.md5(msg_bytes).hexdigest()[:8]
    
    def _forward_message_to_brokers(self, msg_id, parts):
        """Forward message to all brokers that have users in the target room."""
        room = self._extract_room_from_message(parts)
        if not room:
            return
        
        target_brokers = self._get_brokers_with_room_users(room)
        
        for broker_id in target_brokers:
            if broker_id != self.broker_id and msg_id not in self.forwarded_messages:
                self._forward_message_to_broker(broker_id, msg_id, parts)
                self.forwarded_messages.add(msg_id)
    
    def _forward_message_to_broker(self, target_broker_id, msg_id, parts):
        """Forward message to a specific broker via inter-broker PUB."""
        if not self.is_cluster:
            return
        
        target_broker = broker_discovery.get_broker_by_id(target_broker_id)
        if not target_broker:
            return
        
        # Format inter-broker message
        original_msg = b"".join(parts).decode('utf-8', errors='ignore')
        inter_msg = f"MESSAGE:{self.broker_id}:{msg_id}|{original_msg}"
        
        self.broker_pub.send(inter_msg.encode('utf-8'))
<<<<<<< HEAD
=======
        
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
        print(f"[BROKER-{self.broker_id}] Forwarded message {msg_id} to broker {target_broker_id}")
    
    def _handle_message_from_client(self, parts: list):
        """
        Handle message from client (audio, video, text, heartbeat).
        
        Updates last_seen timestamp and broadcasts to other clients.
        """
        try:
            sender_name = None
            
            # Format 1: Video [room, sender, msg_id, timestamp, payload]
            if len(parts) == 5:
                sender_name = parts[1].decode('utf-8', errors='ignore')
            
            # Format 2: Text/Audio/Heartbeat ("SALA:TIPO:NOME:ID|payload")
            elif len(parts) == 1:
                header_parts = parts[0].split(b"|", 1)
                if len(header_parts) >= 1:
                    header_str = header_parts[0].decode('utf-8', errors='ignore')
                    header_pieces = header_str.split(":")
                    if len(header_pieces) >= 3:
                        sender_name = header_pieces[2]
            
            # Update session (heartbeat check)
            if sender_name and sender_name in self.active_users:
                self.active_users[sender_name]["last_seen"] = time.time()
                
                # Broadcast heartbeat globally
                if "HEARTBEAT" in parts[0].decode('utf-8', errors='ignore'):
                    self._broadcast_heartbeat_event(sender_name)
        
        except Exception:
            pass
        
        # Generate message ID and check for cross-broker forwarding
        msg_id = self._generate_message_id(parts)
        self._forward_message_to_brokers(msg_id, parts)
        
        # Relay message to subscribers
        self.backend.send_multipart(parts)
    
    def _cleanup_inactive_users(self, current_time: float):
        """Remove users who haven't sent messages for SESSION_TIMEOUT seconds."""
        dead_users = []
        
        for user, info in self.active_users.items():
            if current_time - info["last_seen"] > SESSION_TIMEOUT:
                dead_users.append(user)
        
        for user in dead_users:
            room = self.active_users[user]["room"]
            print(f"[BROKER-{self.broker_id}] '{user}' disconnected (timeout)")
            del self.active_users[user]
            
            # Remove from global registry
            if user in self.known_users_global:
                del self.known_users_global[user]
            
            # Broadcast logout
            self._broadcast_logout_event(user)
            
            # Inject system message
            aviso = f"{room}:TEXTO:SISTEMA:0|O usuário '{user}' foi desconectado."
            self.backend.send(aviso.encode('utf-8'))
    
    def _cleanup_forwarded_cache(self):
        """Clean up forwarded messages cache to prevent memory leaks."""
        # Keep only the most recent 1000 messages
        if len(self.forwarded_messages) > 1000:
            # Convert to list, keep last 500, convert back to set
            recent = list(self.forwarded_messages)[-500:]
            self.forwarded_messages = set(recent)
    
    def run(self):
        """Main event loop."""
        print(f"[BROKER-{self.broker_id}] Starting event loop...")
        
        try:
            while True:
                socks = dict(self.poller.poll(1000))
                current_time = time.time()
                
                # Handle inter-broker events
                if self.is_cluster and self.broker_sub in socks:
                    try:
                        event = self.broker_sub.recv(zmq.NOBLOCK)
                        self._handle_broker_event(event)
                    except zmq.Again:
                        pass
                
                # Handle authentication
                if self.auth_socket in socks:
                    request = self.auth_socket.recv_string()
                    response = self._handle_login(request)
                    self.auth_socket.send_string(response)
                
                # Handle messages from clients
                if self.frontend in socks:
                    parts = self.frontend.recv_multipart()
                    self._handle_message_from_client(parts)
                
                # Handle subscriptions
                if self.backend in socks:
                    subscription = self.backend.recv()
                    self.frontend.send(subscription)
                
                # Cleanup inactive users periodically
                self._cleanup_inactive_users(current_time)
                
                # Cleanup forwarded messages cache
                self._cleanup_forwarded_cache()
        
        except KeyboardInterrupt:
            print(f"\n[BROKER-{self.broker_id}] Shutting down...")
        
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Close all sockets and context."""
<<<<<<< HEAD
        print(f"[BROKER-{self.broker_id}] Cleaning up...")
        
        # Stop dynamic discovery
        if self._registry_client:
            try:
                self._registry_client.unregister_broker(self.broker_id)
                print(f"[BROKER-{self.broker_id}] ✓ Unregistered from registry")
            except Exception as e:
                print(f"[BROKER-{self.broker_id}] Unregister error: {e}")
        
        if self._udp_discovery:
            self._udp_discovery.stop()
            print(f"[BROKER-{self.broker_id}] ✓ UDP discovery stopped")
        
        # Stop heartbeat thread
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            # The thread will stop when _registry_client is set to None
            self._registry_client = None
            self._heartbeat_thread.join(timeout=2)
        
        # Close sockets
=======
>>>>>>> 7aa82b6a024539eabc686ecf584dd7bfe1858eb8
        self.frontend.close()
        self.backend.close()
        self.auth_socket.close()
        
        if self.is_cluster:
            self.broker_pub.close()
            self.broker_sub.close()
        
        self.context.term()
        print(f"[BROKER-{self.broker_id}] Shutdown complete")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Broker node for distributed video conference system"
    )
    parser.add_argument(
        "--broker-id",
        type=int,
        default=0,
        help="Broker ID in cluster (default: 0)"
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    try:
        broker_discovery.validate_broker_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create and run broker
    try:
        broker = BrokerNode(args.broker_id)
        broker.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
