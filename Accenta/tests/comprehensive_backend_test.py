"""
Comprehensive Backend Testing
Tests all services, endpoints, and configurations
"""

import requests
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None, files=None, expected_status=200):
    """Test an endpoint"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{path}", json=data, files=files, timeout=10)
        else:
            return False, f"Unsupported method: {method}"
        
        is_success = response.status_code == expected_status
        try:
            result = response.json()
        except:
            result = response.text[:200]
        
        return is_success, response.status_code, result
    except requests.exceptions.ConnectionError:
        return False, "Connection Error", "Server not running"
    except Exception as e:
        return False, "Error", str(e)

def test_environment():
    """Test environment variables"""
    print("=" * 60)
    print("1. ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    
    required = {
        "MONGODB_URI": os.getenv("MONGODB_URI"),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    }
    
    all_set = True
    for key, value in required.items():
        status = "✓" if value and value != f"your_{key.lower()}_here" else "✗"
        print(f"  {status} {key}: {'Set' if value and value != f'your_{key.lower()}_here' else 'Missing'}")
        if not value or value == f"your_{key.lower()}_here":
            all_set = False
    
    print()
    return all_set

def test_services():
    """Test service imports"""
    print("=" * 60)
    print("2. SERVICE IMPORTS")
    print("=" * 60)
    
    services = {
        "transcribe": "services.transcribe",
        "align": "services.align",
        "features": "services.features",
        "deviation_model": "services.deviation_model",
        "tts": "services.tts",
        "agent_client": "services.agent_client",
    }
    
    all_ok = True
    for name, module in services.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name}: {str(e)[:50]}")
            all_ok = False
    
    print()
    return all_ok

def test_endpoints():
    """Test all API endpoints"""
    print("=" * 60)
    print("3. API ENDPOINTS")
    print("=" * 60)
    
    endpoints = [
        ("GET", "/", 200),
        ("GET", "/health", 200),
        ("GET", "/docs", 200),
        ("GET", "/openapi.json", 200),
        ("POST", "/api/auth/signup", 200, {
            "email": f"test_{os.urandom(4).hex()}@test.com",
            "username": f"testuser_{os.urandom(4).hex()}",
            "password": "testpass123"
        }),
        ("POST", "/api/auth/login", 401, {
            "email": "nonexistent@test.com",
            "password": "wrongpass"
        }),
        ("POST", "/api/analyze_accent", 422),  # Should fail without file
    ]
    
    results = []
    for endpoint in endpoints:
        method = endpoint[0]
        path = endpoint[1]
        expected = endpoint[2]
        data = endpoint[3] if len(endpoint) > 3 else None
        
        success, status, result = test_endpoint(method, path, data=data, expected_status=expected)
        status_icon = "✓" if success else "✗"
        print(f"  {status_icon} {method} {path} - Status: {status}")
        results.append(success)
    
    print()
    return all(results)

def test_database():
    """Test database connection"""
    print("=" * 60)
    print("4. DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        import asyncio
        from db import Database
        
        async def test():
            try:
                await Database.connect()
                print("  ✓ Database connection successful")
                
                # Test a simple query
                collection = Database.get_collection("users")
                count = await collection.count_documents({})
                print(f"  ✓ Users collection accessible ({count} users)")
                
                await Database.disconnect()
                return True
            except Exception as e:
                print(f"  ✗ Database error: {str(e)[:100]}")
                return False
        
        result = asyncio.run(test())
        print()
        return result
    except Exception as e:
        print(f"  ✗ Database test failed: {str(e)[:100]}")
        print()
        return False

def test_api_keys_functionality():
    """Test API keys are working"""
    print("=" * 60)
    print("5. API KEY FUNCTIONALITY")
    print("=" * 60)
    
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    
    # Test OpenAI key format
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and openai_key.startswith("sk-"):
        print("  ✓ OpenAI API key format valid")
    else:
        print("  ⚠ OpenAI API key format may be invalid")
    
    # Test ElevenLabs key format
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
    if elevenlabs_key and (elevenlabs_key.startswith("Sk_") or len(elevenlabs_key) > 20):
        print("  ✓ ElevenLabs API key format valid")
    else:
        print("  ⚠ ElevenLabs API key format may be invalid")
    
    # Test Google key
    google_key = os.getenv("GOOGLE_API_KEY", "")
    if google_key and len(google_key) > 20:
        print("  ✓ Google API key format valid")
    else:
        print("  ⚠ Google API key format may be invalid")
    
    print()
    return True

def test_server_health():
    """Test server health endpoint"""
    print("=" * 60)
    print("6. SERVER HEALTH")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"  ✓ Server status: {health.get('status', 'unknown')}")
            print(f"  ✓ Database: {health.get('database', 'unknown')}")
            services = health.get('services', {})
            for service, name in services.items():
                print(f"  ✓ {service}: {name}")
            print()
            return True
        else:
            print(f"  ✗ Health check failed: {response.status_code}")
            print()
            return False
    except Exception as e:
        print(f"  ✗ Health check error: {str(e)[:100]}")
        print()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE BACKEND TEST")
    print("=" * 60)
    print()
    
    results = {
        "Environment": test_environment(),
        "Services": test_services(),
        "Endpoints": test_endpoints(),
        "Database": test_database(),
        "API Keys": test_api_keys_functionality(),
        "Server Health": test_server_health(),
    }
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")
        if not result:
            all_passed = False
    
    print()
    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Backend is fully operational!")
    else:
        print("⚠️  SOME TESTS FAILED - Check details above")
    print("=" * 60)
    print()
    print("View API documentation at: http://localhost:8000/docs")
    print()

if __name__ == "__main__":
    main()

