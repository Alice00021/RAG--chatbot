from dotenv import load_dotenv
import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import  TelegramNetworkError, TelegramRetryAfter
import httpx
from db_operations import authorize_user, init_db, add_user, add_chat, add_message, update_chat_status
from producer import send_to_queue
from consumer import consume_messages

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
async def rag_message(message: types.Message, **kwargs):
    pool = kwargs.get("pool")
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    is_authorized, user_id = await authorize_user(telegram_id, pool)

    if is_authorized:
        logger.info(f"Пользователь: {user_id} есть в системе")
        
    else:
        await message.reply("Вы не авторизованы. Сначала зарегистрируйтесь в системе.")
        logger.info(f"Пользователя: {telegram_id} {username} {first_name} {last_name} нет в системе")
        try:
            await add_user(pool, telegram_id, username, first_name, last_name)
            logger.info("Пользователь добавлен в бд")
        except Exception as e:
            logger.error(f"Ошибка: {e}. Пользователь не был добавлен в БД")
 

    try:
        chat_id = await add_chat(pool, user_id)  
        logger.info(f"Чат {chat_id} пользователя: {user_id}")
    except Exception as e:
        logger.error(f"Ошибка: {e}. Не найден чат и не был создан")
        await message.reply("Не удалось создать чат. Попробуйте позже.")
        return

    user_query = message.text.strip()
    logger.info(f"Сообщение пользователя {user_query}")
    try:
        await add_message(pool, chat_id, 'USER', user_query)
        logger.info(f"Сообщение добавлено в таблицу")
    except Exception as e:
        logger.error(f"Ошибка: {e}. Сообщение не было добавлено")
        await message.reply("Не удалось сохранить сообщение. Попробуйте позже.")
        return

    message_data = {
        'message': message.model_dump_json(),
        'user_query': user_query,
        'chat_id': message.chat.id 
    }
    await send_to_queue(message_data)
    
async def main() -> None:
    bot = Bot(token=API_TOKEN)
    pool = await init_db()
    consumer_task = asyncio.create_task(consume_messages(pool, bot))
    try:
        logger.info("Запуск бота")
        await dp.start_polling(bot, pool=pool)
    except Exception as e:
        logger.error(f"Ошибка polling: {e}")
    finally:
        logger.info("Остановка бота")
        consumer_task.cancel()
        await bot.session.close()
         
if __name__ == '__main__':
    asyncio.run(main())
