import logging
import sys
from rag import RAG

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

if __name__ == "__main__":
    logger.info("Запуск теста метода _load_knowledge_base...")
    test_load_knowledge_base()