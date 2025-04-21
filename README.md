# Telegram бот с RAG (Retrieval-Augmented Generation)

Бот с искусственным интеллектом, использующий технологию RAG для ответов на вопросы на основе вашей базы знаний.

## Быстрый старт

### Что нужно перед началом

- Установленный Docker (версия 20.10 или новее)
- Ключ от Telegram бота (получаем у [@BotFather](https://t.me/BotFather))
- API-ключ DeepSeek (для модели deepseek-r1) (можно взять у OpenRouter)

### 1. Установка

```bash
git clone https://github.com/Alice00021/RAG--chatbot.git
cd RAG--chatbot
```

### 2. Настройка окружения

## 2.1 Создайте файл .env в папке RAG:

```bash
HF_HOME=./.cache 
TOKENIZERS_PARALLELISM=false 
CHROMA_DB_PATH=./chroma_db
```
## 2.2 Создайте файл .env в папке LLM
```bash
OPENAI_API_KEY=ваш_ключ_deepseek_r1 или другой модели
```
## 2.3 Создайте файл .env в папке APIgateway
```bash
RAG_SERVICE_URL=http://localhost:8000
LLM_SERVICE_URL=http://localhost:8001
```
## 2.4 Создайте файл .env в папке telegram_bot
```bash
API_KEY=ваш_ключ_от_telegram_bot
API_GATEWAY_URL=http://localhost:8002
```
### 3. Запуск через docker-compose
```bash
docker-compose up --build
docker-compose start
```

## Решение проблем с SELinux (только для Linux)

Если Вы запускате на linux, то могут возникнуть проблемы с knowladge_base из-за SELinux.
Необходимо изменить контекст безопасности для директории ./RAG/knowledge_base.
```bash
sudo chcon -Rt svirt_sandbox_file_t ./RAG/knowledge_base
```




