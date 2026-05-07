"""
Centralized Broker Registry Server

This server maintains a registry of all active brokers in the cluster.
Brokers register themselves and send periodic heartbeats.
Clients can query the registry to discover available brokers.
"""

import socket
import threading
import time
import json
from typing import Dict, List
from shared import config


class BrokerRegistry:
    """Central registry for broker discovery."""

    def __init__(self):
        self.brokers = {}  # broker_id -> broker_info + metadata
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._running = False

    def start_cleanup_thread(self):
        """Start background thread to clean up dead brokers."""
        def cleanup_worker():
            while self._running:
                time.sleep(30)  # Check every 30 seconds
                self._cleanup_dead_brokers()

        self._running = True
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()

    def stop_cleanup_thread(self):
        """Stop the cleanup thread."""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

    def register_broker(self, broker_info: Dict) -> bool:
        """Register or update a broker in the registry."""
        with self._lock:
            broker_id = broker_info["broker_id"]
            self.brokers[broker_id] = {
                **broker_info,
                "last_heartbeat": time.time(),
                "registered_at": time.time()
            }
            print(f"✓ Broker {broker_id} registered/updated")
            return True

    def unregister_broker(self, broker_id: int) -> bool:
        """Remove a broker from the registry."""
        with self._lock:
            if broker_id in self.brokers:
                del self.brokers[broker_id]
                print(f"✓ Broker {broker_id} unregistered")
                return True
            return False

    def heartbeat(self, broker_id: int) -> bool:
        """Update heartbeat timestamp for a broker."""
        with self._lock:
            if broker_id in self.brokers:
                self.brokers[broker_id]["last_heartbeat"] = time.time()
                return True
            return False

    def get_all_brokers(self) -> List[Dict]:
        """Get list of all registered brokers."""
        with self._lock:
            # Return only broker info, not metadata
            return [
                {k: v for k, v in broker.items()
                 if k not in ["last_heartbeat", "registered_at"]}
                for broker in self.brokers.values()
            ]

    def _cleanup_dead_brokers(self):
        """Remove brokers that haven't sent heartbeat recently."""
        cutoff = time.time() - config.REGISTRY_TIMEOUT
        with self._lock:
            dead_brokers = [
                broker_id for broker_id, broker in self.brokers.items()
                if broker["last_heartbeat"] < cutoff
            ]

            for broker_id in dead_brokers:
                print(f"✗ Broker {broker_id} removed (no heartbeat)")
                del self.brokers[broker_id]


class RegistryServer:
    """TCP server for broker registry operations."""

    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.REGISTRY_HOST
        self.port = port or config.REGISTRY_PORT
        self.registry = BrokerRegistry()
        self.server_socket = None
        self._running = False

    def start(self):
        """Start the registry server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.registry.start_cleanup_thread()
        self._running = True

        print(f"📋 Registry server started on {self.host}:{self.port}")

        try:
            while self._running:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("Registry server shutting down...")
        finally:
            self.stop()

    def stop(self):
        """Stop the registry server."""
        self._running = False
        self.registry.stop_cleanup_thread()
        if self.server_socket:
            self.server_socket.close()

    def _handle_client(self, client_socket: socket.socket, addr):
        """Handle a client connection."""
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                return

            request = json.loads(data)
            response = self._process_request(request)

            client_socket.send(json.dumps(response).encode())

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            response = {"status": "error", "message": str(e)}
            try:
                client_socket.send(json.dumps(response).encode())
            except:
                pass
        finally:
            client_socket.close()

    def _process_request(self, request: Dict) -> Dict:
        """Process a registry request."""
        action = request.get("action")

        if action == "register":
            broker_info = request.get("broker")
            if not broker_info:
                return {"status": "error", "message": "Missing broker info"}

            success = self.registry.register_broker(broker_info)
            return {"status": "ok" if success else "error"}

        elif action == "unregister":
            broker_id = request.get("broker_id")
            if broker_id is None:
                return {"status": "error", "message": "Missing broker_id"}

            success = self.registry.unregister_broker(broker_id)
            return {"status": "ok" if success else "error"}

        elif action == "heartbeat":
            broker_id = request.get("broker_id")
            if broker_id is None:
                return {"status": "error", "message": "Missing broker_id"}

            success = self.registry.heartbeat(broker_id)
            return {"status": "ok" if success else "error"}

        elif action == "get_brokers":
            brokers = self.registry.get_all_brokers()
            return {"status": "ok", "brokers": brokers}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}


def main():
    """Main function to run the registry server."""
    server = RegistryServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Shutting down registry server...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()