from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from rag import RAG
import uvicorn

app = FastAPI(title= "RAG")

class Query(BaseModel):
    query : str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

logger = logging.getLogger(__name__)

rag = RAG(knowledge_base="knowledge_base")

@app.post("/query")
async def process_query_with_context(request:Query):
    if not  request.query.strip():
        logger.warning(f"Пользователь отправил пустой запрос")
        raise HTTPException(status_code = 400,detail= "Некорректный запрос. Пользователь отправил пустой запрос")
    try:
        query_with_context = await rag.get_query_with_context(request.query)
        return {"query_with_context":query_with_context}
    except ValueError as e:
        logger.error(f"Ошибка значения: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        logger.error(f"Ошибка таймаута: {e}")
        raise HTTPException(status_code=504, detail="Время ожидания запроса истекло")
    except Exception as e:
        logger.warning(f"Ошибка: {e}")
        raise HTTPException(status_code = 500, detail=str(e))


if __name__=='__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

