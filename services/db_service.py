from chromadb import Collection

class DBService:
    """
    Извлекает документы, проверяет их наличие, если нет -> поиск по всей бд,
    форматирует выход chromadb в словарь.
    """
    def __init__(self, db_collection: Collection ):
        self.collection = db_collection
    

    def retrieve(self, query_embedding, filters, n_results: int = 50):
        """
        Извлекает список документов для нейросети
        """
        data = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=filters
                )
        data = self._format_results(data)
        
        # добавим fallback если нейронка на json-e ошиблась и из базы данных ничего не вывелось
        results = self._fallback(query_embedding, data, n_results)

        return results


    def _fallback(self, query_embedding, data, n_results: int = 50):
        """
        Фолл-бек функция, в случае если база данных ничего не вернула (сломанные фильтры),
        происходит глобальный поиск без фильтров
        """
        if len(data["documents"]) == 0:
            results = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=n_results
                    )
            print("\nПрокнул fall-back\n")
            return self._format_results(results)
        else:
            return data
        
        
    def _format_results(self, raw_data):
        """
        Форматирует выход ChromaDB в словарь
        """
        return {
                "documents":raw_data["documents"][0],
                "metadatas":raw_data["metadatas"][0],
                "distances":raw_data["distances"][0],
            }