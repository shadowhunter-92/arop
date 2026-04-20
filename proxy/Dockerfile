FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install deps first (separate layer — cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Lifespan in main.py handles migrations + seeding on startup
CMD ["sh", "-c", "echo CONTAINER_STARTED && echo PORT=$PORT && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} 2>&1"]
