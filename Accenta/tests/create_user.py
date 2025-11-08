"""
Script to create a test user
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def create_user(email, username, password):
    """Create a new user"""
    url = f"{BASE_URL}/api/auth/signup"
    data = {
        "email": email,
        "username": username,
        "password": password
    }
    
    print(f"Creating user: {username} ({email})")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        user = response.json()
        print("✓ User created successfully!")
        print(f"  User ID: {user['user_id']}")
        print(f"  Email: {user['email']}")
        print(f"  Username: {user['username']}")
        return user
    else:
        print(f"✗ Failed to create user: {response.status_code}")
        print(f"  Error: {response.json()}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 4:
        email = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]
    else:
        # Default test user
        email = "test@accenta.com"
        username = "testuser"
        password = "testpass123"
        print("Using default test user credentials")
        print()
    
    user = create_user(email, username, password)
    
    if user:
        print("\n" + "=" * 60)
        print("User created successfully!")
        print("=" * 60)
        print(f"You can now login with:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")

