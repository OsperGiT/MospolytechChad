import json
from utils.config import detector_system_input, system_input
from ollama import AsyncClient

class LLMService:
    def __init__(self, ollama_client: AsyncClient, ollama_model: str = "gemma3:12b"):
        self.client = ollama_client
        self.model = ollama_model

    async def detect_meta(self, query):
            """
            Определяет метаданные запроса, чистит запрос для эмбеддинга
            """
            content = await self._get_raw_json(query)
            try:
                meta = json.loads(self._clean_json(content))
            except:
                print("Внимание: не удалось извлечь метаданные из ответа")


            return meta


    async def ask_llm(self, context_text, user_history, user_input, stream = False):
        """
        Возваращает ответ нейросети
        """
        full_system_prompt = system_input.format(
            context_temp = context_text,
            user_input_temp = user_input
        )

        messages = [{"role": "system", "content": full_system_prompt}]
        messages.extend(user_history)
        messages.append({"role": "user", "content": user_input})

        response = await self.client.chat(
            model=self.model,
            messages=messages,
            stream=stream,
            options={"temperature" : 0.2}
        )

        return response


    async def _get_raw_json(self, query: str):
        """
        Возвращает json файл для поиска по метаданным
        """
        query_lower = query.lower()

        response = await self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": detector_system_input},
                {"role": "user", "content": query_lower}
            ],
            format = 'json',
            stream = False,
            options={"temperature": 0.2}
        )
        return response.message.content
    

    def _clean_json(self, content: str) -> str:
        """
        Убирает ```json и ``` вокруг JSON, чтобы json.loads работал
        """
        start = content.find("{")
        end = content.rfind("}")
        return content[start:(end + 1)]
    
    