from dotenv import load_dotenv
import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import  TelegramNetworkError, TelegramRetryAfter
import httpx

log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(os.path.join(log_dir, 'telegram_bot.log'))

logging.basicConfig(
    level = logging.INFO,
    handlers=[console_handler, file_handler],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
load_dotenv()

API_TOKEN = os.getenv('API_KEY')
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL')

if not API_TOKEN:
    logger.error("API_TOKEN не найден в переменных окружения. Проверьте файл .env")
    raise ValueError("API_TOKEN не найден в переменных окружения. Проверьте файл .env")

dp = Dispatcher()

@dp.message()
async def rag_message(message: types.Message):
    user_query = message.text.strip()
    logger.info(f"Сообщение пользователя {user_query}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_GATEWAY_URL}/query",
                json={"query": user_query},
                timeout=30.0
            )
            response.raise_for_status()
            answer = response.json().get("response")
            logger.info(f"Ответ для {message.from_user.id}: {answer}")
        await message.answer(answer)
    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка HTTP статуса: {e.response.status_code} - {e.response.text}")
        await message.answer("Ошибка при обработке запроса. Попробуйте еще раз.")
    except httpx.RequestError as e:
        logger.error(f"Ошибка запроса: {e}")
        await message.answer("Ошибка подключения. Попробуйте еще раз.")
    except TelegramNetworkError as e:
        logger.error(f"Ошибка сети Telegram: {e}")
        await message.answer("Ошибка сети Telegram. Попробуйте еще раз.")
    except TelegramRetryAfter as e:
        logger.error(f"Ошибка Telegram RetryAfter: {e}")
        await message.answer("Слишком много запросов. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await message.answer("Что-то пошло не так. Попробуйте еще раз.")

async def main() -> None:
    bot = Bot(token=API_TOKEN)
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
