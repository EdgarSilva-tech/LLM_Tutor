# 🧪 Guia de Testes - API Gateway e Microserviços

## Pré-requisitos
1. Todos os serviços rodando: `docker-compose up --build -d`
2. Aguardar ~30 segundos para inicialização completa

## 1. 🔧 Verificar Status dos Containers
```bash
docker-compose ps
```
**Esperado:** Todos os serviços devem estar "Up"

## 2. 🌐 Testar NGINX API Gateway
```bash
curl -v http://localhost:8080/health
```
**Esperado:** Resposta `healthy` com status 200 OK.

## 3. 🔐 Testar Serviço de Autenticação

### Signup (Cadastro)
```bash
curl -X POST "http://localhost:8080/auth/signup" \
-H "Content-Type: application/json" \
-d '{"username": "testuser", "email": "test@example.com", "full_name": "Test User", "password": "testpassword"}'
```
**Esperado:** JSON com os detalhes do utilizador criado.

### Login (Obter Token)
```bash
curl -X POST "http://localhost:8080/auth/token" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=testuser&password=testpassword"
```
**Esperado:** JSON com `access_token`.
**Copie o token** para usar nos próximos testes!

### Verificar Usuário Logado
```bash
# Substitua SEU_TOKEN_AQUI pelo token que obteve
export TOKEN="SEU_TOKEN_AQUI"

curl -X GET http://localhost:8080/auth/users/me/ \
-H "Authorization: Bearer $TOKEN"
```
**Esperado:** Dados do usuário `testuser`.

## 4. 🤖 Testar Serviços Protegidos

### RAG Service - Fazer uma Pergunta
```bash
curl -X POST "http://localhost:8080/rag/question-answer" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{"question": "What is the derivative of 2x^2?"}'
```
**Esperado:** Uma resposta em JSON com a resposta à pergunta.

### Evaluation Service - Avaliar uma Resposta
```bash
curl -X POST "http://localhost:8080/evaluation/eval-service/evaluate_answer" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{"question": "What is the derivative of 2x^2?", "answer": "4x"}'
```
**Esperado:** Um JSON com a avaliação (`correct_answer`, `feedback`, `score`).

### Quiz Service - Gerar um Quiz
```bash
curl -X POST "http://localhost:8080/quiz/generate-quiz" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{"topic": "calculus", "num_questions": 3}'
```
**Esperado:** Um JSON com uma lista de perguntas para o quiz.

## 5. 🗄️ Verificar Bases de Dados

### Listar Bases de Dados
```bash
docker exec llm_tutor-postgres-1 psql -U postgres -l
```
**Esperado:** Bases `Users`, `Khan_Academy`, `Evaluation`, `llm_tutor_db`

### Verificar Tabelas (exemplo - Auth Service)
```bash
docker exec llm_tutor-postgres-1 psql -U postgres -d Users -c "\dt"
```
**Esperado:** Tabela `user_auth` se o serviço já foi usado

## 🚨 Resolução de Problemas Comuns

### Container não inicia
```bash
docker-compose logs nome_do_serviço
```

### Erro de conexão PostgreSQL
- Verificar se PostgreSQL está rodando: `docker-compose ps postgres`
- Verificar logs: `docker-compose logs postgres`

### Erro de autenticação 401
- Verificar se o token não expirou
- Verificar se está usando o formato correto: `Bearer TOKEN`

### NGINX retorna 502 Bad Gateway
- Algum serviço não está respondendo
- Verificar logs de todos os serviços

## ✅ Checklist de Sucesso

- [ ] Todos os containers estão "Up"
- [ ] NGINX responde (mesmo que 404)
- [ ] Signup funciona
- [ ] Login retorna token
- [ ] `/auth/users/me/` retorna dados do usuário
- [ ] Todos os health checks funcionam
- [ ] Bases de dados estão criadas
- [ ] Logs não mostram erros críticos

## 🎯 Próximos Passos

Se todos os testes passaram:
1. **Implementar endpoints específicos** de cada serviço
2. **Adicionar rate limiting** no NGINX
3. **Configurar SSL/HTTPS** para produção
4. **Adicionar monitoramento** e métricas
5. **Criar testes automatizados** mais robustos

