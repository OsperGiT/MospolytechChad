from db import create_collection

collection = create_collection("docs")

# получить первые 5 документов

results = collection.get(include=["documents", "metadatas"])

for doc, meta in zip(results["documents"], results["metadatas"]):
    print(f"Text: {doc[:50]}...")  # первые 50 символов текста
    print(f"Metadata: {meta}\n")

