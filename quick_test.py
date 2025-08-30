h
#!/usr/bin/env python3
"""
Script rápido para testar endpoints específicos
"""
import requests
import json

def test_endpoint(method, url, data=None, headers=None):
    """Testa um endpoint específico"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            if isinstance(data, dict) and "Content-Type" not in (headers or {}):
                response = requests.post(url, params=data, timeout=10)
            else:
                response = requests.post(url, data=data, headers=headers, timeout=10)
        
        print(f"📍 {method.upper()} {url}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print("-" * 50)
        return response
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("-" * 50)
        return None

if __name__ == "__main__":
    print("🧪 TESTE RÁPIDO DE ENDPOINTS\n")
    
    # Teste 1: NGINX health
    test_endpoint("GET", "http://localhost/health")
    
    # Teste 2: Signup
    signup_data = {
        "username": "quicktest",
        "email": "quick@test.com",
        "full_name": "Quick Test",
        "password": "test123"
    }
    response = test_endpoint("POST", "http://localhost/auth/signup", signup_data)
    
    # Teste 3: Login
    login_data = {
        "username": "quicktest",
        "password": "test123"
    }
    response = test_endpoint("POST", "http://localhost/auth/token", login_data)
    
    if response and response.status_code == 200:
        try:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"🔑 Token obtido: {token[:30]}...")
            
            # Teste 4: Endpoint protegido
            headers = {"Authorization": f"Bearer {token}"}
            test_endpoint("GET", "http://localhost/auth/users/me/", headers=headers)
            
        except Exception as e:
            print(f"❌ Erro ao processar token: {e}")
