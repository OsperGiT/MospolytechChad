from db import create_collection

collection = create_collection("docs")

# получить первые 5 документов

results = collection.get(include=["documents", "metadatas"])
# print(len(results["documents"]))

for doc, meta in zip(results["documents"], results["metadatas"]):
    print(f"Text: {doc}")  # первые 50 символов текста
    print(f"Metadata: {meta}\n")