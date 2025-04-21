from fastapi import FastAPI, HTTPException , Request, status
import os 
import logging
import sys
import uvicorn
import httpx
from pydantic import BaseModel
from prompts import SYSTEM_PROMPT
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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

if not RAG_SERVICE_URL or not LLM_SERVICE_URL :
    logger.error("RAG_SERVICE_URL или LLM_SERVICE_URL не найден в переменных окружения. Проверьте файл .env")
    raise ValueError("RAG_SERVICE_URL или LLM_SERVICE_URL не найден в переменных окружения. Проверьте файл .env")

class QueryRequest(BaseModel):
    query: str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

class QueryResponse(BaseModel):
    response: str

@app.post('/query')
async def send_query(request:QueryRequest):
    try:
        logger.info(f"Отправлен запрос к RAG: {request}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RAG_SERVICE_URL}/query",
                json={"query": request.query},
                timeout=15.0
            )
            response.raise_for_status()
            query_with_context = response.json().get("query_with_context")
            if not query_with_context:
                    logger.error("RAG не вернул query_with_context")
                    raise HTTPException(status_code=500, detail="RAG вернул некорректный ответ")
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
            if not response:
                logger.error("LLM не вернул response")
                raise HTTPException(status_code=500, detail="LLM вернул некорректный ответ")
            logger.info(f"Получен ответ от LLM: {response}")
            return {"response": response}
    except ValueError as e:
        logger.error(f"Ошибка валидации запроса: {e}")
        raise HTTPException(status_code=400, detail=str(e))  
    except TimeoutError as e:
        logger.error(f"Ошибка таймаута: {e}")
        raise HTTPException(status_code=504, detail="Время ожидания запроса истекло")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise HTTPException(status_code=500, detail='Ошибка сервера')
    
if __name__=='__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8002)

