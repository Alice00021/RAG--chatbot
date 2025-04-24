import aio_pika
from dotenv import load_dotenv
import os
import logging
import json
import asyncio

load_dotenv()

RABBITMQ_URL = os.getenv('RABBITMQ_URL')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_to_queue(message):
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        routing_key = 'request'
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange('telegram_bot', aio_pika.ExchangeType.DIRECT)
            await exchange.publish(aio_pika.Message(body=json.dumps(message).encode()), routing_key=routing_key)
            logger.info(f"Сообщение отправлено в очередь: {message}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


if __name__ == '__main__':
    # Пример использования
    example_message = {
        'message': 'Example message',
        'user_query': 'Example query',
        'chat_id': 12345
    }
    asyncio.run(send_to_queue(example_message))    