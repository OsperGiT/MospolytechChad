from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
load_dotenv()

# закомментить если нет токена
os.environ["HF_TOKEN"]=os.getenv("HF_TOKEN")
EMBEDDING_NAME = os.getenv("EMBEDDING_NAME")

print("Загружаем модель эмбеддингов...")
model = SentenceTransformer(EMBEDDING_NAME)
print("Модель загружена")

def get_embedding(chunks_text):
    """
    texts: список строк
    возвращает список эмбеддингов
    """
    return model.encode(chunks_text, convert_to_tensor=True).tolist()