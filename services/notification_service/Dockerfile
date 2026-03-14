FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/notification_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service into a monorepo-like layout inside the container
RUN mkdir -p /app/services/notification_service
COPY services/notification_service/ /app/services/notification_service/

# Enable absolute imports and current-service short imports
ENV PYTHONPATH="/app:/app/services/notification_service"

EXPOSE 8006

# Start the service
CMD ["uvicorn", "services.notification_service.main:app", "--host", "0.0.0.0", "--port", "8006", "--workers", "2"]