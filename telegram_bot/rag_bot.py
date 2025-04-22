from dotenv import load_dotenv
import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import  TelegramNetworkError, TelegramRetryAfter
import httpx
from db_operations import authorize_user, init_db, add_user, add_chat, add_message, update_chat_status

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
async def rag_message(message: types.Message,**kwargs):
    pool = kwargs.get("pool")
    telegram_id = message.from_user.id
    first_name =message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    try:
        await add_user(pool, telegram_id, username, first_name, last_name)
        logger.info("Пользователь добавлен в бд")
    except Exception as e:
        logger.error(f"Ошибка: {e}. Пользователь не был добавлен в БД")

    is_authorized, user_id = await authorize_user(telegram_id, pool)

    if not is_authorized:
        await message.reply("Вы не авторизованы. Сначала зарегистрируйтесь в системе.")
        logger.info(f"Пользователя: {telegram_id} {username} {first_name} {last_name} нет в системе")
        return
    else:
        logger.info(f"Пользователь: {user_id} есть в системе")

    try:
        chat_id = await add_chat(pool, telegram_id)
        logger.info(f"Чат{chat_id} пользователя: {telegram_id}")
    except Exception as e:
        logger.error(f"Ошибка: {e}. Не найден чат и не был создан")

    user_query = message.text.strip()
    logger.info(f"Сообщение пользователя {user_query}")
    try:
        await add_message(pool, chat_id, 'USER', user_query)
        logger.info(f"Сообщение добавлено в таблицу")
    except Exception as e:
        logger.error(f"Ошибка: {e}. Сообщение не было добавлено")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_GATEWAY_URL}/query",
                json={"query": user_query},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            answer = response.json().get("response")
            logger.info(f"Ответ для {user_id}: {answer}")

        requires_operator = result.get("requires_operator", False)

        if not requires_operator:
            await update_chat_status(pool, chat_id, 'OPERATOR_NEEDED')
            logger.info(f"Чат {chat_id} помечен как OPERATOR_NEEDED")
            await message.answer(answer + "\nВаш запрос передан оператору.")
        else:
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
    pool = await init_db()
    try:
        logger.info("Запуск бота")
        await dp.start_polling(bot, pool=pool)
    except Exception as e:
        logger.error(f"Ошибка polling: {e}")
    finally:
        logger.info("Остановка бота")
        await bot.session.close()
         
if __name__ == '__main__':
    asyncio.run(main())
