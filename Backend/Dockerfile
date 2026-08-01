FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so this layer is cached independently of code changes
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Pre-download the sentence-transformer model (~90 MB) so container startup is predictable
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY src/ /app/src/

WORKDIR /app/src

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
