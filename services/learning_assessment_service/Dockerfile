FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/learning_assessment_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service into a monorepo-like layout inside the container
RUN mkdir -p /app/services/learning_assessment_service
COPY services/learning_assessment_service/ /app/services/learning_assessment_service/

# Enable absolute imports and current-service short imports
ENV PYTHONPATH="/app:/app/services/learning_assessment_service"

EXPOSE 8005

CMD ["uvicorn", "services.learning_assessment_service.main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "2"]
