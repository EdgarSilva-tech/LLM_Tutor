from infra.redis_cache import redis_client


def test_redis_connection():
    try:
        # Teste básico
        print(f"✅ Redis conectado! Valor: {redis_client}")
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        print(f"✅ Redis conectado! Valor: {value}")

        # Limpar teste
        redis_client.delete("test_key")
        assert True

    except Exception as e:
        print(redis_client)
        print(f"❌ Erro na conexão Redis: {e}")
        assert False


if __name__ == "__main__":
    test_redis_connection()
