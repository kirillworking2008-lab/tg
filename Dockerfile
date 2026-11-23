FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

# Сессия и .env монтируются через volume / env_file (см. docker-compose.yml)
RUN mkdir -p /app/data

CMD ["python", "main.py"]
