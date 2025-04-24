import aio_pika
import aiohttp
from dotenv import load_dotenv
import os
import logging
import json
from db_operations import update_chat_status, init_db
import asyncio
from aiogram import Bot

load_dotenv()

RABBITMQ_URL = os.getenv('RABBITMQ_URL')
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_message(message_data, bot: Bot, **kwargs):
    pool = kwargs.get("pool")
    user_query = message_data['user_query']
    chat_id = message_data['chat_id']
    chat_id_in_telegram = message_data['chat_id_in_telegram']
    logger.info(f"chat_id_in_telegram: {chat_id_in_telegram}")

    try:
        logger.info(f"Отправка запроса к {API_GATEWAY_URL}/query с данными: {user_query}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_GATEWAY_URL}/query",
                json={"query": user_query},
                timeout=30.0
            ) as response:
                response.raise_for_status()
                result = await response.json()
                answer = result.get("response")
                logger.info(f"Ответ для {chat_id}: {answer}")

        requires_operator = result.get("requires_operator", False)
        logger.info(f"requires_operator: {requires_operator}")
        if requires_operator:
            await update_chat_status(pool, chat_id, 'OPERATOR_NEEDED')
            logger.info(f"Чат {chat_id} помечен как OPERATOR_NEEDED")
            await bot.send_message(chat_id_in_telegram, "Ваш запрос передан оператору.")
        else:
            await bot.send_message(chat_id_in_telegram, answer)

    except aiohttp.ClientResponseError as e:
        logger.error(f"Ошибка HTTP статуса: {e.status} - {e.message}")
        await bot.send_message(chat_id_in_telegram,"Ошибка при обработке запроса. Попробуйте еще раз.")
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка запроса: {e}")
        await bot.send_message(chat_id_in_telegram,"Ошибка подключения. Попробуйте еще раз.")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await bot.send_message(chat_id_in_telegram,"Что-то пошло не так. Попробуйте еще раз.")

async def consume_messages(pool, bot:Bot):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange('telegram_bot', aio_pika.ExchangeType.DIRECT)
        queue = await channel.declare_queue('request_queue', durable=True)
        await queue.bind(exchange, 'request')

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    message_data = json.loads(message.body.decode())
                    await process_message(message_data,bot=bot, pool=pool)

async def main():
    pool = await init_db()
    await consume_messages(pool)

if __name__ == '__main__':
    asyncio.run(main())