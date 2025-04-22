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
    
async def main():
    pool = await init_db()
    await init_db(pool)
    

