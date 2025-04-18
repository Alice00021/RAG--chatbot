from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging
from rag import RAG
import uvicorn

app = FastAPI(title= "RAG")

class Query(BaseModel):
    query : str

load_dotenv()

OPENAI_TOKEN = os.getenv('OPENAI_API_KEY')

logger = logging.getLogger(__name__)

if not OPENAI_TOKEN:
    logger.error("OPENAI_TOKEN не найден в переменных окружения. Проверьте файл .env")
    raise ValueError("OPENAI_TOKEN не найден в переменных окружения. Проверьте файл .env")

rag = RAG(openai_token=OPENAI_TOKEN, knowledge_base="knowledge_base")

@app.post("/query")
async def process_query_with_context(request:Query):
    try:
        query_with_context = await rag.get_query_with_context(request.query)
        return {"query_with_context":query_with_context}
    except Exception as e:
        logger.warning(f"Ошибка: {e}")

if __name__=='__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000)




