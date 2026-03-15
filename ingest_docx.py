from docx import Document
from typing import List
from db import create_collection, add_documents

# =========================
# 1️⃣ Функция для извлечения текста из DOCX
# =========================
def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    full_text = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:  # игнорируем пустые строки
            full_text.append(text)

    # Соединяем абзацы через двойной перенос для логики chunking
    return "\n\n".join(full_text)

# =========================
# 2️⃣ Функция разбиения текста на чанки с перекрытием
# =========================
def chunk_text_with_context(text: str, chunk_size: int = 150, overlap: int = 50) -> List[str]:
    paragraphs = text.split("\n\n")
    chunks = []

    for para in paragraphs:
        words = para.split()
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start = max(end - overlap, end)  # перекрытие
    return chunks

# =========================
# 3️⃣ Функция подготовки чанков с метаданными
# =========================
def prepare_chunks_from_docx(file_path: str, topics: str, subtopics: List[str],
                             chunk_size: int = 150, overlap: int = 50):
    text = extract_text_from_docx(file_path)
    chunks = chunk_text_with_context(text, chunk_size=chunk_size, overlap=overlap)
    metadatas = [{"topics": topics, "subtopics": subtopics} for _ in chunks]
    return chunks, metadatas

# =========================
# Пример использования
# =========================
file_path = "E://RAG_Documents//clear//РАСПИСАНИЕ.docx"  # путь к твоему docx файлу
topics = "расписание"
# subtopics = ["обучение", "практика", "научные исследования", "FAQ"]

chunks, metadatas = prepare_chunks_from_docx(file_path, topics, subtopics = None)

collection_name = create_collection("docs")
add_documents(collection_name, chunks, topics)

# Проверим первые 2 чанка
for i in range(2):
    print(f"--- Chunk {i+1} ---")
    print(chunks[i])  # первые 200 символов
    print(metadatas[i])