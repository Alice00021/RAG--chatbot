FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    g++ \
    make \
    #Удаляет кеш пакетов после установки 
    && rm -rf /var/lib/apt/lists/* 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV HF_HOME=/app/.cache \
    TOKENIZERS_PARALLELISM=false \
    CHROMA_DB_PATH=/app/chroma_db

CMD ["python", "main.py"]
