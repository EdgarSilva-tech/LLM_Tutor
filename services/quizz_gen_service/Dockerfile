FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY ./services/quizz_gen_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/quizz_gen_service/ .

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
