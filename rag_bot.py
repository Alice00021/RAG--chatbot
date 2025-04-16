from dotenv import load_dotenv
import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramAPIError
from rag import RAG
from prompts import SYSTEM_PROMPT

os.environ['HF_HOME'] = os.getenv('HF_HOME', os.path.join(os.path.dirname(__file__), '.cache'))
os.environ['TOKENIZERS_PARALLELISM'] = os.getenv('TOKENIZERS_PARALLELISM', 'false')
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(os.path.join(log_dir, 'bot.log'))
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
                {"role": "system", "content":  SYSTEM_PROMPT},
                {"role": "user", "content": query_with_context}
            ])
        logger.info(f"Ответ от API: {completion}")
        if completion.error:
            #logger.error(f"Ошибка от API: {completion.error}")
            await message.answer(f"Ошибка от API: {completion.error['message']}")
            return
        try:
            response = completion.choices[0].message.content
            if not response:
                raise ValueError("Модель вернула пустой ответ")
        except (IndexError, AttributeError) as e:
            logger.error(f"Ошибка обработки ответа модели: {e}")
            raise ValueError("Модель не вернула корректный ответ")
        
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
