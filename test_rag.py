import logging
import sys
from rag import RAG
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_load_knowledge_base():
    
    openai_token = "dummy_token"

    try:
        rag = RAG(openai_token=openai_token, knowledge_base="knowledge_base")
        documents = rag._load_knowledge_base()

        logger.info(f"Загружено {len(documents)} документов:")
        for i, doc in enumerate(documents):
            logger.info(f"\nДокумент {i + 1}:")
            logger.info(f"Метаданные: {doc.metadata}")
            logger.info(f"Содержимое:\n{doc.page_content}")
    
    except Exception as e:
        logger.error(f"Ошибка при тестировании _load_knowledge_base: {e}")
        sys.exit(1)

def test_initialize_vector_store():
    openai_token = "dummy_token"

    try:
        rag = RAG(openai_token=openai_token, knowledge_base="knowledge_base")
        documents = rag._load_knowledge_base()
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        logger.info("Загрузка существующего векторного хранилища")
        chroma_db = Chroma.from_documents(documents, embeddings, persist_directory="chroma_db")
        chroma_db.persist()
        logger.info("Векторное хранилище создано и сохранено.")
        logger.info(f"Векторное хранилище: {chroma_db}")
        return chroma_db
    except Exception as e:
        logger.error(f"Ошибка при тестировании _load_knowledge_base: {e}")
        sys.exit(1)
    


if __name__ == "__main__":
    logger.info("Запуск теста метода _initialize_vector_store")
    test_initialize_vector_store()