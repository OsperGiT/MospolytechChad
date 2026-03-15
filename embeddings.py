from sentence_transformers import SentenceTransformer

from config import MODEL_NAME

print("Загружаем модель эмбеддингов...")
model = SentenceTransformer(MODEL_NAME)
print("Модель загружена")

def get_embedding(chunks_text):
    """
    texts: список строк
    возвращает список эмбеддингов
    """
    return model.encode(chunks_text, convert_to_tensor=True).tolist()