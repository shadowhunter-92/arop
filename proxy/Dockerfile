FROM python:3.13-slim

WORKDIR /app

# Install deps first (separate layer — cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "python migrations/run_migrations.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
