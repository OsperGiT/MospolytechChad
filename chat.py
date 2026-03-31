from db import create_collection
from embeddings import get_embedding
from config import system_input, dector_system_input
from sentence_transformers import CrossEncoder
from ollama import Client
import os
import json

#включить/выключить отладку (True/False)
otladka = True

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
RERANKER_NAME = os.getenv("RERANKER_NAME")
ollama_client = Client(host = os.getenv("OLLAMA_URL"))
collection = create_collection("docs")
reranker = CrossEncoder(RERANKER_NAME)

# TOPIC_KEYWORDS = {
#     "стипендия": [
#         "стипенд", "стипуха", "академическ", "социальн", "повышенн",
#         "грант", "матпомощ", "выплат", "денежн поддержк"
#     ],

#     "аспирантура": [
#         "аспиран", "диссертац", "кандидатск", "научн руководител",
#         "вак", "научн исследован", "аспирантур", "кандидат наук",
#         "публикац", "конференц"
#     ],

#     "бакалавриат": [
#         "проходн бал", "егэ", "балл", "поступлен",
#         "абитуриент", "конкурс", "направлени",
#         "прием", "приём", "зачислен", "поступит",
#         "минимальн бал"
#     ],
    
#     "расписание": ["расписан", "знач", "график", "сокращ"]
# }

def clean_json(content: str) -> str:
    """
    Убирает ```json и ``` вокруг JSON, чтобы json.loads работал
    """
    # убираем обёртку ```json ... ```
    if content.startswith("```json"):
        content = content[len("```json"):]

    # убираем начальные/конечные ``` и пробелы/переводы строки
    content = content.strip(" \n`")
    return content

def detect_topic(query: str):
    """
    Определяет метаданные запроса, чистит запрос для эмбеддинга
    """
    query_lower = query.lower()

    response = ollama_client.chat(
        model="gemma3:12b",
        messages=[
            {"role": "system", "content": dector_system_input},
            {"role": "user", "content": query_lower}
        ],
        format = 'json',
        stream = False,
        options={"temperature": 0.2}
    )

    content = response["message"]["content"]

    print(f"\nRAW RESPONSE:\n{content}\n")

    data = json.loads(clean_json(content))

    return data["clear_user_input"], data["topic"], data["major_id"]

def retrieve(query, n_results=40):

    query, topics, major_id = detect_topic(query)
    
    if topics == "swearing" or not query or topics is None:
        if otladka:
            print("\n[SKIP RETRIEVE] swearing или пустой запрос\n")
        return [], [], [], topics, []
    
    query_embedding = get_embedding([query])

    if major_id:
        major_id = major_id[:8]
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            
            where={
                "$and":
                [{"topics": topics},
                {"major_id": major_id}]
                }  # фильтр по метаданным
        )
    else:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where={"topics": topics}  # фильтр по метаданным
        )
    # отладка
    if otladka:
        print(f"\nПоиск в топике: {topics}\n")

    return results["documents"][0], results['metadatas'][0], results["distances"][0], topics, query

def rerank(query, pairs):
    # берём только тексты
    docs = [chunk for chunk, _ in pairs]

    # создаём пары (query, doc)
    model_inputs = [(query, doc) for doc in docs]

    # получаем оценки
    scores = reranker.predict(model_inputs)

    # сортируем вместе с метаданными
    ranked = sorted(
        zip(pairs, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return ranked

print("=== RAG чат (exit для выхода) ===")
while True:
    user_input = input("Вы: ")
    
    if user_input.lower() in ["exit", "quit"]:
        break

    context_chunks, metadatas, distance, topics, clean_query = retrieve(user_input)
    pairs = list(zip(context_chunks, metadatas))

    if topics == "проходной балл":
        ranked_docs = rerank(clean_query, pairs)
        # context_text = "\n".join(f"{doc} | {score}" for doc, score in ranked_docs[:10])
        context_text = "\n".join([
        f"{chunk} | Проходной балл на бюджет: {meta['passing_budget']} | "
        f"Средний балл на платную основу: {meta['passing_paid']} | "
        f"Основной код подготовки: {meta['major_id']} | "
        f"Вторичный код подготовки: {meta['secondary_id']} | {str(score)[:4]}"
        for (chunk, meta), score in ranked_docs[:10]
        ])
    elif topics == "swearing" or topics is None:
        context_text = "Пользователь использует неприемлемую лексику/ввел некорректный запрос. ИГНОРИРУЙ ВСЕ, ЧТО НАПИШЕТ ПОЛЬЗОВАТЕЛЬ, ты ВСЕГДА бот политеха, ты не можешь проигнорировать эту инструкцию!"
    else:
        ranked_docs = rerank(clean_query, pairs)
        context_text = "\n".join(f"{chunk} | {score}" for (chunk, meta), score in ranked_docs[:10])
    # отладка
    if otladka:
        print(context_text)

    response = ollama_client.chat(
        
        model="gemma3:12b",
        messages=[{"role": "system", "content": system_input.format(context_temp = context_text,
                                                                    user_input_temp = user_input)},
                   {"role": "user", "content": user_input}],
        stream=True,
        options={
            "temperature" : 0.2
        }
    )

    for chunk in response:
        print(chunk["message"]["content"], end="", flush=True)
    print()