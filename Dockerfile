FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    #Удаляет кеш пакетов после установки 
    && rm -rf /var/lib/apt/lists/* 

RUN mkdir -p /app/chroma_db /app/knowledge_base /app/.cache \
    && chown -R 1000:1000 /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV HF_HOME=/app/.cache \
    TOKENIZERS_PARALLELISM=false \
    KNOWLEDGE_BASE_PATH=/app/knowledge_base \
    CHROMA_DB_PATH=/app/chroma_db

USER 1000:1000

CMD ["python", "rag_bot.py"]

