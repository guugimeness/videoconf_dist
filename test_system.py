#!/usr/bin/env python3
"""
System functionality test script

Tests:
1. Registry server startup and basic operations
2. Broker registration with registry
3. UDP broadcast discovery
4. Client-broker connection flow
"""

import sys
import time
import subprocess
import signal
import socket
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shared import config, broker_discovery

def test_registry_connection():
    """Test direct TCP connection to registry."""
    print("\n=== Testing Registry Connection ===")
    try:
        registry = broker_discovery.get_registry_client()
        
        # Test broker registration
        test_broker = {
            "broker_id": 99,
            "host": "127.0.0.1",
            "publish_port": 7777,
            "subscribe_port": 7778,
            "auth_port": 7779,
            "broker_pub_port": 7780,
            "broker_sub_port": 7781,
        }
        
        result = registry.register_broker(test_broker)
        if result:
            print("✓ Registry registration successful")
        else:
            print("✗ Registry registration failed")
            return False
        
        # Test getting brokers
        brokers = registry.get_all_brokers()
        print(f"✓ Retrieved {len(brokers)} brokers from registry")
        
        # Test heartbeat
        result = registry.heartbeat(99)
        if result:
            print("✓ Registry heartbeat successful")
        else:
            print("✗ Registry heartbeat failed")
            return False
        
        # Cleanup
        registry.unregister_broker(99)
        print("✓ Broker unregistered from registry")
        
        return True
        
    except Exception as e:
        print(f"✗ Registry connection failed: {e}")
        return False

def test_udp_discovery():
    """Test UDP broadcast discovery."""
    print("\n=== Testing UDP Discovery ===")
    try:
        udp = broker_discovery.get_udp_discovery()
        
        # Start listening
        udp.start_listening()
        print("✓ UDP listener started")
        
        # Wait for potential broadcasts
        time.sleep(2)
        
        # Check discovered brokers
        discovered = udp.get_discovered_brokers()
        print(f"✓ Found {len(discovered)} brokers via UDP")
        
        if discovered:
            for broker in discovered:
                print(f"  - Broker {broker['broker_id']} at {broker['host']}")
        
        udp.stop()
        print("✓ UDP discovery stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ UDP discovery failed: {e}")
        return False

def test_broker_selection():
    """Test broker selection for users."""
    print("\n=== Testing Broker Selection ===")
    try:
        # Get broker config
        brokers = config.BROKER_LIST
        if not brokers:
            print("✗ No brokers in BROKER_LIST")
            return False
        
        print(f"✓ Found {len(brokers)} brokers in static config")
        
        # Test user routing
        test_users = ["alice", "bob", "charlie"]
        routing = {}
        
        for user in test_users:
            broker = broker_discovery.get_broker_for_user(user)
            routing[user] = broker["broker_id"]
            print(f"✓ {user} -> Broker {broker['broker_id']}")
        
        # Test consistency
        for user in test_users:
            broker2 = broker_discovery.get_broker_for_user(user)
            if routing[user] == broker2["broker_id"]:
                print(f"✓ {user} consistently routed to Broker {broker2['broker_id']}")
            else:
                print(f"✗ {user} routing inconsistent!")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Broker selection failed: {e}")
        return False

def test_socket_binding():
    """Test if broker socket ports are available."""
    print("\n=== Testing Socket Binding ===")
    try:
        brokers = config.BROKER_LIST
        
        for broker in brokers[:1]:  # Test first broker only
            broker_id = broker["broker_id"]
            host = broker["host"]
            
            ports = {
                "publish": broker["publish_port"],
                "subscribe": broker["subscribe_port"],
                "auth": broker["auth_port"],
            }
            
            print(f"\nBroker {broker_id} on {host}:")
            
            for port_name, port in ports.items():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind((host, port))
                    print(f"  ✓ {port_name} port {port} available")
                    sock.close()
                except OSError as e:
                    print(f"  ✗ {port_name} port {port} in use: {e}")
                    sock.close()
                    return False
        
        return True
        
    except Exception as e:
        print(f"✗ Socket binding test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("System Functionality Test Suite")
    print("=" * 60)
    print(f"Discovery Mode: {config.SERVICE_DISCOVERY_MODE}")
    print(f"UDP Broadcast: {config.ENABLE_UDP_BROADCAST}")
    print(f"Registry: {config.REGISTRY_HOST}:{config.REGISTRY_PORT}")
    
    results = {}
    
    # Test 1: Socket binding
    print("\n[1/4] Socket Binding Test")
    results["Socket Binding"] = test_socket_binding()
    
    # Test 2: Broker selection
    print("\n[2/4] Broker Selection Test")
    results["Broker Selection"] = test_broker_selection()
    
    # Test 3: UDP discovery
    print("\n[3/4] UDP Discovery Test")
    results["UDP Discovery"] = test_udp_discovery()
    
    # Test 4: Registry connection
    print("\n[4/4] Registry Connection Test")
    results["Registry"] = test_registry_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASSED" if passed_test else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
