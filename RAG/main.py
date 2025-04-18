from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from rag import RAG
import uvicorn

app = FastAPI(title= "RAG")

class Query(BaseModel):
    query : str

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
    except Exception as e:
        logger.warning(f"Ошибка: {e}")
        raise HTTPException(status_code = 500, detail=str(e))


if __name__=='__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

