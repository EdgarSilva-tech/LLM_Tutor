#!/usr/bin/env python3
"""
Script de teste para verificar se o API Gateway e
todos os serviços estão funcionando
"""

import requests
import time
import sys

# Configurações
BASE_URL = "http://localhost:8080"
TEST_USER = {
    "username": "Edgar_Silva",
    "email": "edgardasilva10@hotmail.com",
    "full_name": "Edgar Costa Neves da Silva",
    "password": "test123",
}


def test_service_health(service_name, path="/"):
    """Testa se um serviço está respondendo"""
    try:
        response = requests.get(f"{BASE_URL}{path}", timeout=5)
        print(f"✅ {service_name}: Status {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name}: Erro - {e}")
        return False


def test_auth_signup():
    """Testa o cadastro de usuário"""
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=TEST_USER, timeout=10)

        if (
            response.status_code == 200 or response.status_code == 400
        ):  # 400 if user already exists
            print(f"✅ Signup: Status {response.status_code}")
            return True
        else:
            print(f"❌ Signup: Status {response.status_code} - {response.text[:100]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Signup: Erro - {e}")
        return False


def test_auth_login():
    """Testa o login e retorna o token"""
    try:
        # Fazer login
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"],
        }

        response = requests.post(f"{BASE_URL}/auth/token", data=login_data, timeout=10)

        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"✅ Login: Token obtido - {token[:20]}...")
            return token
        else:
            print(f"❌ Login: Status {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Login: Erro - {e}")
        return None


def test_protected_endpoint(endpoint, token, service_name, method="GET", data=None):
    """Testa um endpoint protegido com JWT"""
    try:
        headers = {"Authorization": f"Bearer {token}"}

        if method.upper() == "POST":
            response = requests.post(
                f"{BASE_URL}{endpoint}", headers=headers, json=data, timeout=15
            )
        else:
            response = requests.get(
                f"{BASE_URL}{endpoint}", headers=headers, timeout=10
            )

        if response.status_code == 200:
            print(
                f"✅ {service_name}: Endpoint '{endpoint}' funcionando (Status {response.status_code})"
            )
            return True
        else:
            print(
                f"❌ {service_name}: Endpoint '{endpoint}' falhou (Status {response.status_code}) - {response.text[:100]}"
            )
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name}: Erro - {e}")
        return False


def main():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DO API GATEWAY E MICROSERVIÇOS\n")

    # Aguardar serviços iniciarem
    print("⏳ Aguardando serviços iniciarem...")
    time.sleep(5)

    # Teste 1: NGINX API Gateway
    print("\n📋 1. TESTANDO NGINX API GATEWAY")
    test_service_health("NGINX Gateway", "/health")

    # Teste 2: Serviço de Autenticação
    print("\n📋 2. TESTANDO SERVIÇO DE AUTENTICAÇÃO")
    test_auth_signup()
    time.sleep(1)
    token = test_auth_login()

    if not token:
        print("❌ Não foi possível obter token. Parando testes.")
        sys.exit(1)

    # Teste 3: Endpoints protegidos
    print("\n📋 3. TESTANDO ENDPOINTS PROTEGIDOS")
    test_protected_endpoint("/auth/users/me/", token, "Auth Service")

    # RAG Service Test
    rag_data = {"question": "What is the derivative of 2x^2?"}
    test_protected_endpoint(
        "/rag/question-answer", token, "RAG Service", method="POST", data=rag_data
    )

    # Evaluation Service Test
    eval_data = {"question": "What is the derivative of 2x^2?", "answer": "4x"}
    test_protected_endpoint(
        "/evaluation/eval-service/evaluate_answer",
        token,
        "Evaluation Service",
        method="POST",
        data=eval_data,
    )

    # Quiz Service Test
    quiz_data = {
        "topic": "calculus",
        "num_questions": 2,
        "difficulty": "medium",
        "style": "multiple choice",
    }
    test_protected_endpoint(
        "/quiz/generate-quiz", token, "Quiz Service", method="POST", data=quiz_data
    )

    print("\n🎉 TESTES CONCLUÍDOS!")


if __name__ == "__main__":
    main()
