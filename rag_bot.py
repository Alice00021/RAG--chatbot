from dotenv import load_dotenv
import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramAPIError
import openai
from openai import AsyncOpenAI, OpenAI
from rag import RAG

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('bot.log')
logging.basicConfig(
    level = logging.INFO,
    handlers=[console_handler, file_handler],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
load_dotenv()

API_TOKEN = os.getenv('API_KEY')
OPENAI_TOKEN = os.getenv('OPENAI_API_KEY')

if not API_TOKEN or  not OPENAI_TOKEN:
    logger.error("API_TOKEN или OPENAI_TOKEN не найден в переменных окружения. Проверьте файл .env")
    raise ValueError("API_TOKEN или OPENAI_TOKEN не найден в переменных окружения. Проверьте файл .env")

dp = Dispatcher()

rag = RAG(openai_token=OPENAI_TOKEN, knowledge_base="knowledge_base")

@dp.message()
async def rag_message(message: types.Message):
    try:
        query_with_context = await rag.get_query_with_context(message.text)
        completion = await rag.client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=[
                {"role": "system", "content": "Ты полезный ассистент, который отвечает на вопросы, используя предоставленный контекст."},
                {"role": "user", "content": query_with_context}
            ])
        if not completion.choices:
            raise ValueError("Модель не вернула ответ")       
        response = completion.choices[0].message.content
        await message.answer(response)
        logger.info(f"Ответил пользователю {message.from_user.id}: {response}")
    except TelegramAPIError as e:
            logger.error(f"Ошибка Telegram API: {e}")
            await message.answer("Произошла ошибка при отправке сообщения.")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await message.answer("Что-то не так")

async def main() -> None:
    bot = Bot (token= API_TOKEN)
    dp.bot = bot
    try:
        logger.info("Запуск бота")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка polling: {e}")
    finally:
        logger.info("Остановка бота")
        await bot.session.close()
         
if __name__ == '__main__':
    asyncio.run(main())
