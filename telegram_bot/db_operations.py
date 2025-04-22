import asyncpg
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
DB_USER=os.getenv('DB_USER')
DB_NAME=os.getenv('DB_NAME')
DB_PASSWORD=os.getenv('DB_PASSWORD')
DB_HOST=os.getenv('DB_HOST')
DB_PORT=os.getenv('DB_PORT')

async def init_db():
    return await asyncpg.create_pool(
        user = DB_USER,
        database = DB_NAME,
        password = DB_PASSWORD,
        host = DB_HOST,
        port = DB_PORT
        )

async def authorize_user( telegram_id: int, pool) -> tuple[bool, int]:
    async with pool.acquire() as conn:
        user = await conn.fetchrow('SELECT user_id FROM "User" WHERE telegram_id = $1', telegram_id)
        if user:
            return True, user['user_id']
        return False, None

async def add_user(pool, telegram_id: int, username: str, first_name:str, last_name:str):
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO "User"(telegram_id, username, first_name, last_name) VALUES($1, $2, $3, $4 )
        ''', telegram_id, username, first_name, last_name)  

async def add_chat(pool, user_id: int) -> int:
    async with pool.acquire() as conn:
        chat = await conn.fetchrow('SELECT chat_id FROM "Chat" WHERE user_id = $1', user_id)
        if not chat:
            await conn.execute('INSERT INTO "Chat" (user_id) VALUES ($1)', user_id)
            chat = await conn.fetchrow('SELECT chat_id FROM "Chat" WHERE user_id = $1', user_id)
        return chat['chat_id']

async def add_message(pool, chat_id: int, sender_type: str, text: str, responder_id: int = None):
    async with pool.acquire() as conn:
        await conn.execute(
            'INSERT INTO "Message" (chat_id, sender_type, responder_id, text) VALUES ($1, $2, $3, $4)',
            chat_id, sender_type, responder_id, text
        )

async def update_chat_status(pool, chat_id: int, status:str):
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE "Chat" SET status = $2 WHERE chat_id = $1',
            chat_id, status
        )
        
async def main():
    pool = await init_db()
    await init_db(pool)
    

