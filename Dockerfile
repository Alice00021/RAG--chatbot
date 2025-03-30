FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "echo_bot.py"]

