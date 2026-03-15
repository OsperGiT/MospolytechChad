import chromadb
from chromadb.config import Settings
from embeddings import get_embedding
from config import CHROMA_DIR
import uuid

# Создаём клиент
client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_DIR,
        is_persistent=True
    )
)

def create_collection(name="documents"):
    if name in [c.name for c in client.list_collections()]:
        return client.get_collection(name)
    return client.create_collection(name)

# Функия добавления таблиц вроде проходных баллов
def add_documents(collection, chunks_text, topics=None, subtopics_list=None):
    """
    collection       - Chroma коллекция
    chunks_text      - список чанков текста
    topics           - список темы для каждого чанка (или один элемент для всех)
    subtopics_list   - список списков под-тем для каждого чанка
    """
    embeddings = get_embedding(chunks_text)

    for i, text in enumerate(chunks_text):
        metadata = {}

        # добавляем topic
        if topics:
            if isinstance(topics, list):
                metadata["topics"] = topics[i]  # если передан список тем по чанкам
            else:
                metadata["topics"] = topics      # если одна тема для всех

        # добавляем subtopics
        if "очно-заочная" in text:
            metadata["subtopics"] = ["очно-заочная", "проходные баллы"]
        elif "заочная" in text:
            metadata["subtopics"] = ["заочная", "проходные баллы"]
        elif "очная" in text:
            metadata["subtopics"] = ["очная", "проходные баллы"]

        collection.add(
            documents=[text],
            embeddings=[embeddings[i]],
            ids=[str(uuid.uuid4())],
            metadatas=[metadata]
        )

# функция добавления чанков из docx
# def add_documents(collection, chunks_text, topics=None, subtopics_list=None):

#     embeddings = get_embedding(chunks_text)
#     metadata = {}
#     metadata["topics"] = topics

#     for i, text in enumerate(chunks_text):
#         collection.add(
#             documents=[text],
#             embeddings=[embeddings[i]],
#             ids=[str(uuid.uuid4())],
#             metadatas=[metadata]
#         )
#     print("Документы успешно добавлены")