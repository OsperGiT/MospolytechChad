import json
from services.db_service import DBService
from services.emb_service import EMBService
from services.llm_service import LLMService

class RAGEngine:
    """
    Ядро RAG-системы, возвращает ответ ЛЛМ на основе контекста из бд
    """
    def __init__(self, db_collection: DBService, llm_service: LLMService, embedding_model: EMBService):
        self.db = db_collection
        self.llm = llm_service
        self.embedder = embedding_model


    async def get_answer(self, user_query: str, user_history: dict[list], stream: bool = False):
        """
        Пайплайн извлечения и подготовки документов из базы данных.

        Определение мета-данных по запросу пользователя ->
        Сборка фильтра из мета-данных для поиска по базе данных ->
        Получение эмбеддинга запроса, для извлечения 50 наиболее схожих документов (векторов) ->
        Извлечение документов ->
        Реранкинг документов с выбором 10 наиболее релевантных
        """
        meta = await self.llm.detect_meta(user_query)
        filter = self._create_filter(meta)
        
        if filter is not None:
            query_embedding = self.embedder.get_embedding(meta["clear_user_input"])
            db_results = self.db.retrieve(query_embedding, filter, n_results=50)
            reranked_results = self.embedder.rerank(meta["clear_user_input"], db_results["documents"], db_results["metadatas"])
        else: reranked_results = ()

        context_text = self._get_context(reranked_results, meta["topics"])
        self._debug(meta, context_text, ison=True)
        answer = await self.llm.ask_llm(context_text, user_history, user_query, stream)

        return answer


    def create_history(self, user_history: list[dict[str]], user_input: str, response: str, memory: int = 10):
        user_history.append({"role": "user", "content": user_input})
        user_history.append({"role": "assistant", "content": response})

        if len(user_history) > memory:
            user_history = user_history[-memory:]

        return user_history


    def _get_context(self, reranked_results, topics) -> str:
        """
        Создает контекст для нейросети на основе метаданных
        """
        try:
            if topics == "проходной балл":
                context_text = "\n".join([
                f"{chunk} | Проходной балл на бюджет: {meta['passing_budget']} | "
                f"Средний балл на платную основу: {meta['passing_paid']} | "
                f"Основной код подготовки: {meta['major_id']} | "
                f"Вторичный код подготовки: {meta['secondary_id']}"
                for (chunk, meta, _) in reranked_results
                ])
            elif topics == "swearing" or topics is None:
                context_text = "Пользователь использует неприемлемую лексику/ввел некорректный запрос"
            else:
                context_text = "\n\n".join(f"{chunk}" for (chunk, _, _) in reranked_results)

        except Exception as e:

            context_text = "Произошла какая-то ошибка, контекст пустой, попроси пользователя переформулировать запрос"
            print(f"\nПроизошла следующая ошибка:\n{e}\n")
        
        return context_text
    

    def _debug(self, data_json, context_text, ison=False):
        """
        Включает вывод в консоль возваращаемого нейросетью json файла и получаемый нейросетью контекст
        """
        if ison:
            data_json = json.dumps(data_json, indent=4, ensure_ascii=False)
            print("\nDEBUG_JSON:\n", data_json, end="\nDEBUG_JSON_END\n")
            print("\nDEBUG_CONTEXT:\n", context_text, end="\nDEBUG_CONTEXT_END\n\n")
        else: return 0

    
    def _create_filter(self, meta: dict):
        """
        Собриает фильтр для поиска по базе данных
        """
        filter = []

        # если введен некорректный запрос
        if (meta["topics"] == "swearing") or (meta["clear_user_input"] is None) or (meta["topics"] is None):
            filter = None
            return filter
        
        # добавляем поиск по топикам
        filter.append({"topics":meta["topics"]})
        
        # добавляем поиск по подтопикам
        if meta["subtopics"] is not None:
            filter.append({"subtopics":meta["subtopics"]})
        
        if meta["major_id"] is not None:
            filter.append({"major_id":meta["major_id"][:8]})

        # объединяем фильтры при помощи $and в случае если их больше двух
        if len(filter) >= 2:
            filter = {"$and": filter}
        elif len(filter) == 1:
            filter = filter[0]

        return filter