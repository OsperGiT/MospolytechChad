import chromadb
from utils.config import CHROMA_DIR

# Создаём клиент
def create_client():
    return chromadb.PersistentClient(path=CHROMA_DIR)