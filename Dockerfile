FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    #Удаляет кеш пакетов после установки 
    && rm -rf /var/lib/apt/lists/* 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV HF_HOME=/app/.cache \
    TOKENIZERS_PARALLELISM=false

CMD ["python", "rag_bot.py"]
