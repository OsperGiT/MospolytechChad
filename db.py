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
def add_documents_structured(collection, chunks, topics=None):
    documents_text = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        direction = chunk.get("direction", "")
        form = chunk.get("form", "")
        profile = chunk.get("profile") or ""
        major_id = chunk.get("major_id") or ""
        secondary_id = chunk.get("secondary_id") or ""

        # Преобразуем баллы в числа, если возможно
        def parse_number(val):
            if val is None:
                return 0
            val = str(val).replace(",", ".").strip()
            try:
                return float(val)
            except:
                return 0

        passing_budget = parse_number(chunk.get("passing_budget"))
        passing_paid = parse_number(chunk.get("passing_paid"))

        # Текст для embedding
        text = f"{direction} ({form})"
        if profile != direction:
            text += f": {profile}"
        documents_text.append(text)

        # Метаданные — только плоские типы
        metadata = {
            "direction": direction,
            "form": form,
            "major_id": major_id,
            "profile": profile,
            "passing_budget": passing_budget,
            "passing_paid": passing_paid,
            "secondary_id": secondary_id,
            "subtopics": ["проходные баллы", form],
        }

        if topics:
            metadata["topics"] = topics if not isinstance(topics, list) else topics[i]

        metadatas.append(metadata)

    # Генерация embeddings
    embeddings = get_embedding(documents_text)

    # Добавляем в ChromaDB
    collection.add(
        documents=documents_text,
        embeddings=embeddings,
        ids=[str(uuid.uuid4()) for _ in chunks],
        metadatas=metadatas
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