FROM python:3.13-slim

WORKDIR /app

# Install dependencies, including postgresql-client for psql
RUN apt-get update && apt-get install -y \
    gcc g++ make \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/rag_service/requirements.txt .
RUN cat requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the wait script first and make it executable
COPY wait-for-postgres.sh .
RUN chmod +x wait-for-postgres.sh

# Copy the service into a monorepo-like layout inside the container
RUN mkdir -p /app/services/rag_service
COPY services/rag_service/ /app/services/rag_service/

# Enable absolute imports and current-service short imports
ENV PYTHONPATH="/app:/app/services/rag_service"

EXPOSE 8002

# Use the wait script to start the service
CMD ["./wait-for-postgres.sh", "postgres", "uvicorn", "services.rag_service.main:app", "--host", "0.0.0.0", "--port", "8002"]