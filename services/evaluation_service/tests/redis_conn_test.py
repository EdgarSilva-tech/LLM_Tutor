from infra.redis_cache import redis_client


def test_redis_connection():
    try:
        # Teste básico
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        print(f"✅ Redis conectado! Valor: {value}")

        # Limpar teste
        redis_client.delete("test_key")

    except Exception as e:
        print(f"❌ Erro na conexão Redis: {e}")


if __name__ == "__main__":
    test_redis_connection()
