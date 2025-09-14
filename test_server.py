#!/usr/bin/env python3
"""
Simple server test script
"""

import requests


def test_server():
    """Test server responses"""

    print("🧪 Testing Flask server...")

    # Test basic endpoints
    endpoints = [
        ("/", "Home page"),
        ("/about", "About page"),
        ("/auth/login", "Login page"),
        ("/auth/register", "Register page"),
    ]

    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://127.0.0.1:5000{endpoint}", timeout=5)
            status = (
                "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            )
            print(f"{status} - {description}: {endpoint}")
        except requests.exceptions.RequestException as e:
            print(f"❌ FAIL - {description}: {endpoint} - {e}")

    # Test authentication
    print("\n🔐 Testing authentication...")
    try:
        # Test login with valid credentials
        login_data = {"email": "admin@pd-triglav.si", "password": "password123"}
        session = requests.Session()
        response = session.post("http://127.0.0.1:5000/auth/login", data=login_data, timeout=5)

        if response.status_code in [200, 302]:  # 302 is redirect after successful login
            print("✅ PASS - Admin login successful")

            # Test accessing dashboard
            dashboard_response = session.get("http://127.0.0.1:5000/dashboard", timeout=5)
            if dashboard_response.status_code == 200:
                print("✅ PASS - Dashboard access after login")
            else:
                print(f"❌ FAIL - Dashboard access: {dashboard_response.status_code}")
        else:
            print(f"❌ FAIL - Admin login: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL - Authentication test: {e}")


if __name__ == "__main__":
    print("🚀 Starting Flask server test...\n")

    # Give instructions
    print("Please run this in another terminal:")
    print("source venv/bin/activate && python3 app.py")
    print("\nThen press Enter to continue testing...")
    input()

    test_server()

    print("\n✅ Server testing complete!")
    print("\nIf all tests passed, your Flask app is working correctly!")
    print("You can access it at: http://127.0.0.1:5000")
