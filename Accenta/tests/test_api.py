"""
Test FastAPI endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test health check endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("\nTesting / endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FastAPI Endpoint Testing")
    print("=" * 60)
    
    root_ok = test_root_endpoint()
    health_ok = test_health_endpoint()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Root endpoint: {'✓' if root_ok else '✗'}")
    print(f"Health endpoint: {'✓' if health_ok else '✗'}")
    print("\nNote: Start the server with: uvicorn backend.app:app --reload")

