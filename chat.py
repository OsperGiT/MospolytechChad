from db import create_collection
from embeddings import get_embedding
from config import system_input
import ollama

#включить/выключить отладку (True/False)
otladka = False

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


def detect_topic(query: str):
    query_lower = query.lower()

    for topics, keywords in TOPIC_KEYWORDS.items():
        for word in keywords:
            if word in query_lower:
                return topics

    return "МФЦ"   # дефолтный топик

def retrieve(query, n_results=15):

    topics = detect_topic(query)

    query_embedding = get_embedding([query])

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where={"topics": topics}   # фильтр по метаданным
    )

    # отладка
    if otladka:
        print(f"\nПоиск в топике: {topics}\n")

    return results["documents"][0], results["distances"][0]

print("=== RAG чат (exit для выхода) ===")
while True:
    user_input = input("Вы: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    context_chunks, distance = retrieve(user_input)
    context_text = "\n".join(context_chunks)

    # отладка
    if otladka:
        for z in range(len(context_chunks)):
            print(context_chunks[z], "  Дистаниция: ",distance[z], "\n")

    response = ollama.chat(
        
        model="gemma3:12b",
        messages=[{"role": "system", "content": system_input.format(context_temp = context_text,
                                                                    user_input_temp = user_input)},
                   {"role": "user", "content": user_input}],
        stream=True,
        options={
            "temperature" : 0.8
        }
    )

    for chunk in response:
        print(chunk["message"]["content"], end="", flush=True)
    print()