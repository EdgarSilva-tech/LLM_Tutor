FROM python:3.13-slim

WORKDIR /app

# Install dependencies, including postgresql-client for psql
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/evaluation_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the wait script first and make it executable
COPY wait-for-postgres.sh .
RUN chmod +x wait-for-postgres.sh

# Copy the rest of the service directory
COPY services/evaluation_service/ .

EXPOSE 8003

# Use the wait script to start the service
CMD ["./wait-for-postgres.sh", "postgres", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"] 