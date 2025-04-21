from dotenv import load_dotenv
import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Request, status
import uvicorn
from pydantic import BaseModel
from openai import AsyncOpenAI, Timeout
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title = "LLM Service")

class LLMRequest(BaseModel):
    query_with_context: str
    system_prompt: str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(os.path.join(log_dir, 'llm.log'))

logging.basicConfig(
    level = logging.INFO,
    handlers=[console_handler, file_handler],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
load_dotenv()

OPENAI_TOKEN = os.getenv('OPENAI_API_KEY')

client = AsyncOpenAI(
    api_key=OPENAI_TOKEN,
    base_url="https://openrouter.ai/api/v1",
)

if  not OPENAI_TOKEN:
    logger.error("OPENAI_TOKEN не найден в переменных окружения. Проверьте файл .env")
    raise ValueError("OPENAI_TOKEN не найден в переменных окружения. Проверьте файл .env")

@app.post('/generate_answer')
async def generate_response(request:LLMRequest):
    if not request.query_with_context.strip():
        logger.warning(f"Пользователь отправил пустой запрос")
        raise HTTPException(status_code = 400,detail= "Некорректный запрос. Пользователь отправил пустой запрос")
    try:
        completion = await client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=[
                {"role": "system", "content":  request.system_prompt},
                {"role": "user", "content": request.query_with_context}
            ])
        logger.info(f"Ответ от API: {completion}")

        try:
            response = completion.choices[0].message.content
            if not response:
                reasoning = getattr(completion.choices[0].message, 'reasoning', None)
                if reasoning:
                    response = reasoning
                    logger.info("Использовано поле reasoning вместо content")
                else:
                    raise ValueError("Модель вернула пустой ответ в content и reasoning")
        except (IndexError, AttributeError) as e:
            logger.error(f"Ошибка обработки ответа модели: {e}")
            raise ValueError("Модель не вернула корректный ответ")
    except Exception as e:
        logger.error(f"Ошибка LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Timeout as e:
        logger.error(f"Ошибка Timeout: {e}")
        raise HTTPException(status_code=504, detail="Время ожидания запроса истекло")
    except Exception as e:
        logger.error(f"Ошибка LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"response": response}

         
if __name__=='__main__':
    uvicorn.run("llm:app", host="0.0.0.0", port=8001)
