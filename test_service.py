#!/usr/bin/env python3
"""
Test script for Pangolin Restart Service
"""

import requests
import time
import sys

SERVICE_URL = "http://localhost:8080"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_get_config():
    """Test getting configuration"""
    print("\nTesting get configuration...")
    try:
        response = requests.get(f"{SERVICE_URL}/config", timeout=10)
        if response.status_code == 200:
            print("✅ Get config passed")
            config = response.json()
            print(f"Current port range: {config['port_range']['min']}-{config['port_range']['max']}")
            return True
        else:
            print(f"❌ Get config failed with status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Get config failed: {e}")
        return False

def test_restart_command():
    """Test the restart command (WARNING: This will actually restart containers!)"""
    print("\nTesting restart command...")
    print("⚠️  WARNING: This will actually restart your Pangolin containers!")
    
    confirm = input("Do you want to proceed? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("Skipping restart test")
        return True
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/restart",
            json={"command": "restart_pangolin"},
            timeout=180  # 3 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Restart command passed")
            print(f"Response: {result}")
            return True
        else:
            print(f"❌ Restart command failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Restart command failed: {e}")
        return False

def test_invalid_command():
    """Test invalid command handling"""
    print("\nTesting invalid command...")
    try:
        response = requests.post(
            f"{SERVICE_URL}/restart",
            json={"command": "invalid_command"},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Invalid command properly rejected")
            return True
        else:
            print(f"❌ Invalid command test failed with status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Invalid command test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Pangolin Restart Service")
    print(f"Service URL: {SERVICE_URL}")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Get Configuration", test_get_config),
        ("Invalid Command", test_invalid_command),
        ("Restart Command", test_restart_command),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔸 {test_name}")
        if test_func():
            passed += 1
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
