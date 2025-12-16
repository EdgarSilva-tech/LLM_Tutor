FROM python:3.13-slim

WORKDIR /app

# Install dependencies, including postgresql-client for psql
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/auth_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the wait script first and make it executable
COPY wait-for-postgres.sh .
RUN chmod +x wait-for-postgres.sh

# Copy the service into a monorepo-like layout inside the container
RUN mkdir -p /app/services/auth_service
COPY services/auth_service/ /app/services/auth_service/

# Enable absolute imports and current-service short imports
ENV PYTHONPATH="/app:/app/services/auth_service"

EXPOSE 8001

# Use the wait script to start the service
CMD ["./wait-for-postgres.sh", "postgres", "uvicorn", "services.auth_service.main:app", "--host", "0.0.0.0", "--port", "8001"]