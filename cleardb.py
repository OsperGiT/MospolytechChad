import chromadb
from chromadb.config import Settings
from config import CHROMA_DIR
from db import create_collection

client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_DIR,
        is_persistent=True
    )
)

# удалить коллекцию
# client.delete_collection("MFC")
# print("Коллекция удалена")

#почистить данные
collection = create_collection("docs")
collection.delete(
    where={"topics":"бакалавриат"}
)
print("Данные из коллекции удалены")