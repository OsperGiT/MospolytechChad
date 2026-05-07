from utils.pipeline import init_db_services 
from ingestion.ingester import IngestManager
from db.manager import DBManager


def _init_collection(manager: DBManager):
    # Выводим доступные коллекции
    collections = manager.inspect_collections()

    col_number = int(input("Выберите номер коллекции с которой вы будете работать: "))

    # Инициализируем выбранную коллекцию
    collection = manager.create_collection(collections[col_number - 1].name)
    return collection


def db_master():
    manager = init_db_services()

    action = input("1 - посмотреть файлы, 2 - добавить файлы, 3 - удалить файлы, 4 - создать коллекцию, 5 - удалить коллекцию, 6 - выйти. Выберите что вы хотите сделать: ")

    if action == "1":
        # Инициализируем коллекцию
        collection = _init_collection(manager)

        # Получаем данные для поиска
        topics = input("'Enter для пропуска' Введите название topics: ")
        subtopics = input("'Enter для пропуска' Введите одно или несколько названий subtopics через запятую: ")
        n_results = input("'Enter для пропуска' Введите количество результатов: ")
        n_of_char = input("'Enter для пропуска' Введите количество символов каждого результата: ")

        # Проверка на отсутствие ввода
        if topics == "":
            topics = None
        else:
            topics = [topics]
        if subtopics == "":
            subtopics = None
        else:
            subtopics = list([subtopic for subtopic in subtopics.split(",")])
        if n_results == "":
            n_results = 10
        else:
            n_results = int(n_results)
        if n_of_char == "":
            n_of_char = None
        else:
            n_of_char = int(n_of_char)
        
        # Делаем поиск по базе данных
        manager.inspect_db(collection, topics, subtopics, n_results, n_of_char)
        return 0
    
    elif action == "2":
        # Инициализируем коллекцию
        collection = _init_collection(manager)

        action2 = input("Какие файлы вы хотие добавить? 1 - Документы, 2 - Структурированные (Проходные баллы): ")
        if action2 == "1":

            path = input("Введите путь до файла: ")
            topics = input("Введите название topics: ")
            subtopics = input("Введите одно или несколько названий subtopics через запятую: ")

            # Проверка на отсутствие ввода
            if topics == "":
                print("topics не может быть пустым")
                db_master()
                return 0
            if subtopics == "":
                print("subtopics не может быть пустым")
                db_master()
                return 0
            else:
                subtopics = list([subtopic for subtopic in subtopics.split(",")])
            
            # Готовим чанки и добавляем в базу данных
            path = path.replace("/", "\\")
            chunks_text = IngestManager(path).prepare_chunks_from_docx()
            manager.add_documents(collection, chunks_text, topics, subtopics)
            return 0
        
        if action2 == "2":

            path = input("Введите путь до файла: ")
            topics = input("Введите название topics: ")

            # Проверка на отсутствие ввода
            if topics == "":
                print("topics не может быть пустым")
                db_master()
                return 0
            
            # Готовим чанки и добавляем в базу данных
            path = path.replace("/", "\\")
            chunks = IngestManager(path).prepare_chunks_from_table()
            manager.add_documents_structured(collection, chunks, topics)
            return 0
        
    elif action == "3":
        # Инициализируем коллекцию
        collection = _init_collection(manager)

        topics = input("'Enter для пропуска' Введите название topics: ")
        subtopics = input("'Enter для пропуска' Введите одно или несколько названий subtopics через запятую: ")

        if topics == "":
            topics = None
        else:
            topics = [topics]
        if subtopics == "":
            subtopics = None
        else:
            subtopics = list([subtopic for subtopic in subtopics.split(",")])

        manager.clear_db(collection, topics, subtopics)
        return 0

    elif action == "4":
        name = input("Введите название коллекции, которую хотите создать: ")
        manager.create_collection(name)
        return 0
    
    elif action == "5":
        manager.delete_collection()
        return 0
    
    elif action == "6":
        return 0
