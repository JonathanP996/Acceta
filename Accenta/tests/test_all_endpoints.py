"""
Comprehensive endpoint testing script
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None, files=None):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{path}", data=data, files=files)
        else:
            return False, f"Unsupported method: {method}"
        
        return response.status_code, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    except Exception as e:
        return None, str(e)

print("=" * 60)
print("Accenta API Endpoint Testing")
print("=" * 60)
print()

# Test 1: Root endpoint
print("1. GET /")
status, response = test_endpoint("GET", "/")
print(f"   Status: {status}")
if isinstance(response, dict):
    print(f"   Response: {json.dumps(response, indent=2)}")
else:
    print(f"   Response: {response[:100]}")
print()

# Test 2: Health endpoint
print("2. GET /health")
status, response = test_endpoint("GET", "/health")
print(f"   Status: {status}")
if isinstance(response, dict):
    print(f"   Response: {json.dumps(response, indent=2)}")
else:
    print(f"   Response: {response[:100]}")
print()

# Test 3: OpenAPI schema
print("3. GET /openapi.json")
status, response = test_endpoint("GET", "/openapi.json")
print(f"   Status: {status}")
if isinstance(response, dict):
    paths = list(response.get("paths", {}).keys())
    print(f"   Available paths: {len(paths)}")
    for path in paths[:5]:
        print(f"     - {path}")
else:
    print(f"   Response: {response[:100]}")
print()

# Test 4: Analyze accent (should fail without file)
print("4. POST /api/analyze_accent (without file - expected to fail)")
status, response = test_endpoint("POST", "/api/analyze_accent")
print(f"   Status: {status}")
if isinstance(response, dict):
    print(f"   Response: {json.dumps(response, indent=2)}")
else:
    print(f"   Response: {response[:100]}")
print()

# Test 5: Docs endpoint
print("5. GET /docs")
try:
    response = requests.get(f"{BASE_URL}/docs")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
    if response.status_code == 200:
        print("   ✓ Swagger UI is accessible")
except Exception as e:
    print(f"   Error: {e}")
print()

print("=" * 60)
print("Test Summary")
print("=" * 60)
print("Open http://localhost:8000/docs in your browser for interactive API testing")

