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
cd rag-bot

2. Настройка окружения

Создайте файл .env в корне проекта с содержимым:

API_KEY=ваш_ключ_от_telegram_bot
OPENAI_API_KEY=ваш_ключ_deepseek_r1

3. Запуск через Docker

docker build -t rag-bot .
docker run -d --name my-rag-bot -v ./chroma_db:/app/chroma_db --env-file .env rag-bot


