import uuid
from chromadb.api import ClientAPI
from chromadb import Collection
from services.emb_service import EMBService

class DBManager:
    def __init__(self, client: ClientAPI, emb_service: EMBService = None):
        self.client = client
        self.emb_service = emb_service
    

    # Создать или найти уже существующую коллекцию
    def create_collection(self, name="docs"):
        """
        На данный момент основная коллекция это docs
        """
        if name in [c.name for c in self.client.list_collections()]:
            print(f"Найдена существующая коллекция: {name}")
            return self.client.get_collection(name)
        
        print(f"Коллекция: {name} создана")
        return self.client.create_collection(name)

    def inspect_collections(self):
        """
        Возваращет доступные коллекции
        """
        collections = self.client.list_collections()
        print(f"На данный момент доступны следующие коллекции: ", end="")

        for i, collect in enumerate(collections):
            if i + 1 < len(collections):
                print(i + 1, collect.name, end = ", ")
            else: print(i + 1, collect.name)

        return collections


    # удалить коллекцию
    def delete_collection(self):
        """
        Функция для удаления коллекций (маловерятно, что пригодится)
        """
        collections = self.inspect_collections()

        num = input("Введите номер какой коллекции, вы хотите удалить: ")

        col_to_del = str(collections[int(num) - 1].name)
        self.client.delete_collection(col_to_del)

        print(f"Коллекция {col_to_del} успешно удалена")


    def add_documents(self, collection: Collection, chunks_text: list, topics: str = None, subtopics_list: str | list = None):
        """
        Функция добавляет чанки из документов в базу данных.
        Один чанк - один абзац.
        """
        # Создаем чанки для эмбеддингов
        embeddings = self.emb_service.get_embedding(chunks_text)
        metadata = {}
        metadata["topics"] = topics
        metadata["subtopics"] = subtopics_list

        collection.add(
            documents=chunks_text,
            embeddings=embeddings,
            ids=[str(uuid.uuid4()) for _ in chunks_text],
            metadatas=[metadata for _ in chunks_text]
        )
        print("Документы успешно добавлены\n")
    

    def add_documents_structured(self, collection: Collection, chunks: str, topics=None):
        """
        Добавляет структурированные документы в коллекцию (базу данных).
        В исходном документе форма обучения должна быть интегрирована в заголовок по второму столбцу.

        Пример:
        Наименование направления подготовки, специальности
        на очное отделение университета в 2025 году (по Москве)
        """
        documents_text = []
        metadatas = []

        for chunk in chunks:
            metadata = self._get_metadata(chunk, topics)
            metadatas.append(metadata)

            chunk_text = self._get_chunk_text(chunk)
            documents_text.append(chunk_text)

        # Генерация embeddings
        embeddings = self.emb_service.get_embedding(documents_text)

        # Добавляем в ChromaDB
        collection.add(
            documents=documents_text,
            embeddings=embeddings,
            ids=[str(uuid.uuid4()) for _ in chunks],
            metadatas=metadatas
        )
        print("Структурированные документы успешно добавлены\n")

    
    # Ислледовать коллекцию (базу данных)
    def inspect_db(self, collection: Collection, topics: list[str] = None, subtopics: list[str] = None, n_results: int = 10, n_of_char: int = None):
        """
        Функция позволяет сделать поиск в базе данных по фильтрам.
        topics, subtopics - обязательно список

        Доступные topics:
        проходной балл, документы

        Доступные subtopoics:
        аспирантура, мфц, наука для обучающихся, общежития, оплата обучения, практика, проектная деятельность, расписание и обозначения, стипендия
        """
        data_filter = self._create_filter(topics, subtopics)

        results = collection.get(
            include=["documents", "metadatas", "embeddings"],
            where=data_filter
        )

        for doc, meta, emb in zip(results["documents"][:n_results], results["metadatas"][:n_results], results["embeddings"]):
            text = doc if n_of_char is None else f"{doc[:n_of_char]}..."
            print(f"\nText: {text}")  # первые x символов текста
            print(f"Metadata: {meta}")
            print(f"Embeddings: {len(emb)}\n")
        print(f"Всего документов: {len(results["ids"])}")


    # Почистить данные внутри коллекции (базы данных)
    def clear_db(self, collection: Collection, topics: list[str] = None, subtopics: list[str] = None):
        """
        Функция позволяет почистить базу данных.
        topics, subtopics - обязательно список

        Доступные topics:
        проходной балл, документы

        Доступные subtopoics:
        аспирантура, мфц, наука для обучающихся, общежития, оплата обучения, практика, проектная деятельность, расписание и обозначения, стипендия
        """
        data_filter = self._create_filter(topics, subtopics)

        if data_filter is None:
            print("Нельзя удалить все данные, определите topics или subtopics")
            return 0
        
        collection.delete(
            where=data_filter
        )
        print("Данные удалены\n")


    def _create_filter(self, topics: list[str] = None, subtopics: list[str] = None):
        """
        Создает фильтр для удаления/поиска данных
        """
        filter = []

        if topics is not None:
            filter.append({"topics": {"$in":topics}})
        
        if subtopics is not None:
            filter.append({"subtopics": {"$in":subtopics}})

        if len(filter) >= 2:
            filter = {"$and":filter}
        elif len(filter) == 1: 
            filter = filter[0]
        elif len(filter) == 0:
            filter = None

        return filter
    

    def _parse_number(self, val):
        """
        Преобразует строку в число (Бюджет и платка)
        """
        if val is None:
            return 0
        val = str(val).replace(",", ".").strip()
        try:
            return float(val)
        except:
            return 0
        
    
    def _get_chunk_text(self, chunk: dict):
        """
        Собирает чанк для embedding - поиска (текстовый поиск)
        """
        direction = chunk.get("direction") or ""
        form = chunk.get("form") or ""
        profile = chunk.get("profile") or ""

        chunk_text = f"{direction} ({form})"
        if profile != "":
            chunk_text += f": {profile}"
        return chunk_text
    
    
    def _get_metadata(self, chunk: dict, topics = None):
        """
        Получает метаданные для структурированных данных (проходные баллы)
        """
        direction = chunk.get("direction") or ""
        form = chunk.get("form") or ""
        profile = chunk.get("profile") or ""
        major_id = chunk.get("major_id") or ""
        secondary_id = chunk.get("secondary_id") or ""

        passing_budget = self._parse_number(chunk.get("passing_budget"))
        passing_paid = self._parse_number(chunk.get("passing_paid"))

        metadata = {
            "direction": direction,
            "form": form,
            "major_id": major_id,
            "profile": profile,
            "passing_budget": passing_budget,
            "passing_paid": passing_paid,
            "secondary_id": secondary_id,
        }

        if topics is not None:
            metadata["topics"] = topics
        return metadata
