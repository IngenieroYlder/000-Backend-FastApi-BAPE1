import requests
import sys

BASE_URL = "http://localhost:8000"

def test_backend():
    print("Testing Backend...")
    
    # 1. Register Company & User
    register_payload = {
        "email": "test@newcompany.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "phone": "1234567890",
        "company_name": "New Tech Co"
    }
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
        if r.status_code == 200:
            print("✅ Registration Successful")
            user_data = r.json()
            print(f"   User ID: {user_data['id']}, Company ID: {user_data.get('company_id')}, Role: {user_data.get('role')}")
        elif r.status_code == 400 and "registrado" in r.text:
             print("⚠️ User already exists (skipping registration)")
        else:
            print(f"❌ Registration Failed: {r.status_code} {r.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Login
    login_payload = {
        "username": "test@newcompany.com",
        "password": "password123"
    }
    r = requests.post(f"{BASE_URL}/auth/login", data=login_payload)
    if r.status_code == 200:
        token = r.json()["access_token"]
        print("✅ Login Successful")
    else:
        print(f"❌ Login Failed: {r.status_code} {r.text}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Product (SaaS Check)
    product_payload = {
        "name": "SaaS Product",
        "price": 99.99,
        "stock": 10,
        "description": "A product for New Tech Co"
    }
    r = requests.post(f"{BASE_URL}/products/", json=product_payload, headers=headers)
    if r.status_code == 200:
        print("✅ Product Mutation Successful")
    else:
        print(f"❌ Product Mutation Failed: {r.status_code} {r.text}")

    # 4. List Products
    r = requests.get(f"{BASE_URL}/products/", headers=headers)
    if r.status_code == 200:
        products = r.json()
        print(f"✅ List Products Successful. Count: {len(products)}")
        # Verify ownership (implicit since we only see our own, but good to check content)
        if len(products) > 0 and products[0]['name'] == "SaaS Product":
             print("   Verified Product ownership.")
    else:
        print(f"❌ List Products Failed: {r.status_code} {r.text}")

if __name__ == "__main__":
    test_backend()
