from sentence_transformers import SentenceTransformer, CrossEncoder

class EMBService:
    """
    Может получить эмбеддинги, провести реранкинг результатов
    """
    def __init__(self, embedding_model: SentenceTransformer = None, reranker_model: CrossEncoder = None):
        self.model = embedding_model
        self.reranker = reranker_model


    def get_embedding(self, texts):
        """
        texts: список чанков/запрос пользователя;
        возвращает список эмбеддингов
        """
        return self.model.encode(texts, convert_to_tensor=True).tolist()
    

    def rerank(self, query: str, documents: list[str], metadatas: list[dict], n_results: int = 10):
        """
        Реранкер получает топ 50 документов и сортирует по значимости для ответа на вопрос,
        возвращает 10 наиболее релевантных по умолчанию
        """
        # создаём пары (query, doc)
        model_inputs = [(query, doc) for doc in documents]

        # получаем оценки
        scores = self.reranker.predict(model_inputs)

        # сортируем вместе с метаданными
        ranked = sorted(
            zip(documents, metadatas, scores),
            key=lambda x: x[2],
            reverse=True
        )
        
        return ranked[:n_results]