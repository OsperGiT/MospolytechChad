import os
from dotenv import load_dotenv
from services.llm_service import LLMService
from services.db_service import DBService
from services.emb_service import EMBService
from db.manager import DBManager
from core.engine import RAGEngine
from ollama import AsyncClient
from sentence_transformers import SentenceTransformer, CrossEncoder
from db.client import create_client

load_dotenv()

def _check_env(requirements: list):
    for key in requirements:
        if not os.getenv(key):
            raise ValueError(f"Критическая ошибка: в файле .env не найдена переменная '{key}'")

def init_rag_services():
    """
    Инициализирует зависимости для использования RAG
    """
    _check_env(["EMBEDDING_NAME","RERANKER_NAME","OLLAMA_URL"])

    # Запрещает использовать прокcи (позволяет избежать ошибок при включенном VPN)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"

    # Проверка на наличие токена Hugging Face (наличие опционально)
    if os.getenv("HF_TOKEN"):
        os.environ["HF_TOKEN"]=os.getenv("HF_TOKEN")
    
    # Инициализация зависимостей
    embedding_model = SentenceTransformer(os.getenv("EMBEDDING_NAME"))
    reranker = CrossEncoder(os.getenv("RERANKER_NAME"), device='cuda')
    ollama_client = AsyncClient(host = os.getenv("OLLAMA_URL"))
    collection = DBManager(create_client()).create_collection()

    # Инициализация сервисов (классов)
    db_serv = DBService(collection)
    llm_serv = LLMService(ollama_client)
    embedding_serv = EMBService(embedding_model, reranker)

    return  RAGEngine(db_serv, llm_serv, embedding_serv)

def init_db_services():
    """
    Инициализирует зависимости для управления БД (коллекциями)
    """
    _check_env(["EMBEDDING_NAME"])

    # Запрещает использовать прокcи (позволяет избежать ошибок при включенном VPN)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"

    # Проверка на наличие токена Hugging Face (наличие опционально)
    if os.getenv("HF_TOKEN"):
        os.environ["HF_TOKEN"]=os.getenv("HF_TOKEN")
    
    # Инициализация зависимостей
    embedding_model = SentenceTransformer(os.getenv("EMBEDDING_NAME"))
    emb_serv = EMBService(embedding_model)

    return  DBManager(create_client(), emb_serv)