FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/quizz_gen_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service into a monorepo-like layout inside the container
RUN mkdir -p /app/services/quizz_gen_service
COPY services/quizz_gen_service/ /app/services/quizz_gen_service/

# Enable absolute imports and current-service short imports
ENV PYTHONPATH="/app:/app/services/quizz_gen_service"

EXPOSE 8004

CMD ["uvicorn", "services.quizz_gen_service.main:app", "--host", "0.0.0.0", "--port", "8004"]
