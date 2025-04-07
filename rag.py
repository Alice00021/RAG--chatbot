import time
import logging
import os
import json
from glob import glob
from typing import List
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import CharacterTextSplitter
from openai import AsyncOpenAI
import torch


logger = logging.getLogger(__name__)

class RAG():
    def __init__(self, openai_token:str, knowledge_base:str, force_reload: bool = False):
        self.knowledge_base_path = knowledge_base
        self.openai_token = openai_token
        self.force_reload = force_reload

        self.client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.openai_token)

        self.llm = ChatOpenAI(
            openai_api_key=self.openai_token,
            openai_api_base="https://openrouter.ai/api/v1",
            model_name="deepseek/deepseek-r1:free",
        )
        self.embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base",
                                                model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"})
        
        self.vector_store = self._initialize_vector_store()

    def _extract_text_from_json(self, creature: dict) -> str:
        
        text_parts = []

        for key in ["scientific_name", "common_name", "mythology", "science", "threats"]:
            if key in creature and creature[key]:
                text_parts.append(f"{key}: {creature[key]}")
        if "habitat" in creature:
            habitat = creature["habitat"]
            if "location" in habitat and habitat["location"]:
                text_parts.append(f"habitat location: {habitat['location']}")
            if "description" in habitat and habitat["description"]:
                text_parts.append(f"habitat description: {habitat['description']}")

        if "appearance" in creature:
            appearance = creature["appearance"]
            for key, value in appearance.items():
                if value:
                    text_parts.append(f"appearance {key}: {value}")

        if "behavior" in creature:
            behavior = creature["behavior"]
            for key, value in behavior.items():
                if value:
                    text_parts.append(f"behavior {key}: {value}")

        return "\n".join(text_parts)
    
    def _load_knowledge_base(self) -> List[Document]:
        logger.info(f"Загрузка базы знаний из {self.knowledge_base_path}...")

        documents = []
        text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=50)

        json_files = glob(os.path.join(self.knowledge_base_path, "*.json"))
        if not json_files:
            logger.error(f"Не найдено JSON-файлов в папке {self.knowledge_base_path}")
            raise FileNotFoundError(f"Не найдено JSON-файлов в папке {self.knowledge_base_path}")
        
        for json_file in json_files:
            logger.info(f"Обработка файла: {json_file}")
            try:
                with open(json_file, 'r', encoding='utf-8') as file :
                    data = json.load(file)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при разборе JSON в файле {json_file}: {e}")
                continue

            if "creatures" not in data:
                logger.warning(f"Файл {json_file} не содержит ключ 'creatures'. Пропускаем.")
                continue
            for creature in data["creatures"]:
                if not creature.get("scientific_name") or not creature.get("common_name"):
                    logger.warning(f"Пропущен элемент без scientific_name или common_name в файле {json_file}: {creature}")
                    continue

                content = self._extract_text_from_json(creature)
                #print(f"Животное{content}")
                metadata = {
                    "scientific_name": creature.get("scientific_name", ""),
                    "common_name":creature.get("common_name", ""),
                    "habitat_location": creature.get("habitat", {}).get("location", ""),
                    "source": json_file
                }
                #print(f"Метаданные: {metadata}")
                
                if len(content) > 500: 
                    chunks = text_splitter.split_text(content)
                    for chunk in chunks:
                        documents.append(Document(page_content=chunk, metadata=metadata))
                else:
                    documents.append(Document(page_content=content, metadata=metadata))
                    
        if not documents:
            logger.error("Не удалось загрузить ни одного документа из базы знаний.")
            raise ValueError("Не удалось загрузить ни одного документа из базы знаний.")
        
        logger.info(f"Загружено {len(documents)} документов из базы знаний.")
        return documents

    def _initialize_vector_store(self) -> Chroma:
        persist_dir = "/app/chroma_db"
        if os.path.exists(persist_dir)  and not self.force_reload:
            logger.info("Загрузка существующего векторного хранилища...")
            return Chroma(persist_directory=persist_dir, embedding_function=self.embeddings)
        else:
            logger.info("Создание векторного хранилища")
            documents = self._load_knowledge_base()
        chroma_db = Chroma.from_documents(documents = documents, embedding = self.embeddings, persist_directory=persist_dir)
        logger.info("Векторное хранилище создано и сохранено.")
        return chroma_db

    async def get_query_with_context(self, query:str) -> str:
        logger.info(f"Поиск релевантного контекста для запроса: {query}")
        relevant_docs = await self.vector_store.asimilarity_search(query, k=2)

        if not relevant_docs:
            logger.warning("Контекст не найден для запроса")
            context = "Контекст отсутствует."
        else:
            context = "\n".join([f"{doc.metadata['common_name']} ({doc.metadata['scientific_name']}): {doc.page_content}" for doc in relevant_docs])
            logger.info(f"Найденный контекст: {context}")

        query_with_context = f"Контекст: {context}\n\nВопрос: {query}"
        logger.info(f"Расширенный запрос: {query_with_context}")
        return query_with_context
