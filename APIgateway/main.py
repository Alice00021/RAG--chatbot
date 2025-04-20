from fastapi import FastAPI, HTTPException
import os 
import logging
import sys
import uvicorn
import httpx
from pydantic import BaseModel
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from prompts import SYSTEM_PROMPT

app = FastAPI(title = 'API Gateway')

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

RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL')
LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL')

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.post('/query')
async def send_query(request:QueryRequest):
    try:
        logger.info("Отправлен запрос к RAG")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RAG_SERVICE_URL}/query",
                json={"query": request.query},
                timeout=15.0
            )
            response.raise_for_status()
            query_with_context = response.json().get("query_with_context")
            logger.info(f"Получен ответ от RAG: {query_with_context}")

            logger.info("Отправлен запрос к LLM")
            llm_response = await client.post(
                f"{LLM_SERVICE_URL}/generate_answer",
                json={"query_with_context": query_with_context,
                    "system_prompt": SYSTEM_PROMPT},
                timeout=60.0
            )
            llm_response.raise_for_status()
            response = llm_response.json().get("response")
            logger.info(f"Получен ответ от LLM: {response}")

            return {"response": response}
        
    except Exception as e:
        logger.error(f"Ошибка метода send_query: {e}")
        raise HTTPException(status_code=500, detail='Ошибка сервера')
    
if __name__=='__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8002)

