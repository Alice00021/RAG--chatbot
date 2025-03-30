from dotenv import load_dotenv
import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types

load_dotenv()

API_TOKEN = os.getenv('API_KEY')
if not API_TOKEN:
    raise ValueError("API_TOKEN не найден в переменных окружения. Проверьте файл .env")

dp = Dispatcher()

@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text)

async def main() -> None:
    bot = Bot (token= API_TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
