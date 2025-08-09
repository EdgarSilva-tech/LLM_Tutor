FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/evaluation_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the specific service directory
COPY services/evaluation_service/ .

EXPOSE 8003

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8003}"] 