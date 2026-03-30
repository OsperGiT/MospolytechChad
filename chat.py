from db import create_collection
from embeddings import get_embedding
from config import system_input, dector_system_input
import ollama
from ollama import Client
import os
import json
#включить/выключить отладку (True/False)
otladka = True

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
ollama_client = Client(host = os.getenv("OLLAMA_URL"))

collection = create_collection("docs")

TOPIC_KEYWORDS = {
    "стипендия": [
        "стипенд", "стипуха", "академическ", "социальн", "повышенн",
        "грант", "матпомощ", "выплат", "денежн поддержк"
    ],

    "аспирантура": [
        "аспиран", "диссертац", "кандидатск", "научн руководител",
        "вак", "научн исследован", "аспирантур", "кандидат наук",
        "публикац", "конференц"
    ],

    "бакалавриат": [
        "проходн бал", "егэ", "балл", "поступлен",
        "абитуриент", "конкурс", "направлени",
        "прием", "приём", "зачислен", "поступит",
        "минимальн бал"
    ],
    
    "расписание": ["расписан", "знач", "график", "сокращ"]
}

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
    query_lower = query.lower()

    response = ollama_client.chat(
        model="gemma3:12b",
        messages=[
            {"role": "system", "content": dector_system_input},
            {"role": "user", "content": query_lower}
        ],
        stream = False,
        options={"temperature": 0.2}
    )

    content = response["message"]["content"]

    print(f"\nRAW RESPONSE:\n{content}\n")

    data = json.loads(clean_json(content))

    return data["clear_user_input"], data["topic"], data["major_id"]

def retrieve(query, n_results=20):

    query, topics, major_id = detect_topic(query)
    
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

    return results["documents"][0], results['metadatas'][0], results["distances"][0], topics

print("=== RAG чат (exit для выхода) ===")
while True:
    user_input = input("Вы: ")
    
    if user_input.lower() in ["exit", "quit"]:
        break
    context_chunks, metadatas, distance, topics = retrieve(user_input)
    if topics == "проходной балл":
        context_text = "\n".join([f"{chunk} | Проходной балл на бюджет: {meta["passing_budget"]} | Средний балл на платную основу: {meta["passing_paid"]} | Основной код подготовки: {meta["major_id"]} | Вторичный код подготовки: {meta["secondary_id"]}" for chunk, meta in zip(context_chunks, metadatas)])
    else:
        context_text = "\n".join(chunk for chunk in context_chunks)
    # отладка
    if otladka:
        if str(topics) == "проходной балл":
            otladka_text = "\n\n".join([f"{chunk} | Проходной балл на бюджет: {meta["passing_budget"]} | Средний балл на платную основу: {meta["passing_paid"]} | Основной код подготовки: {meta["major_id"]} | Вторичный код подготовки: {meta["secondary_id"]} | {i+1}" for i, (chunk, meta) in enumerate(zip(context_chunks, metadatas))])
        else:
            otladka_text = "\n".join(f"{chunk} | {i}" for i, chunk in enumerate(context_chunks))
        print(otladka_text)
        # for z in range(len(context_chunks)):
        #     print(context_chunks[z], "  Дистаниция: ",distance[z], "\n")

    response = ollama_client.chat(
        
        model="gemma3:12b",
        messages=[{"role": "system", "content": system_input.format(context_temp = context_text,
                                                                    user_input_temp = user_input)},
                   {"role": "user", "content": user_input}],
        stream=True,
        options={
            "temperature" : 0.4
        }
    )

    for chunk in response:
        print(chunk["message"]["content"], end="", flush=True)
    print()