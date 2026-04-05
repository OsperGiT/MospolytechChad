import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from ollama import AsyncClient
from config import system_input, dector_system_input
from sentence_transformers import CrossEncoder
import json
from db import create_collection
from embeddings import get_embedding
from config import system_input

load_dotenv()

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 300))
RERANKER_NAME = os.getenv("RERANKER_NAME")

reranker = CrossEncoder(RERANKER_NAME)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

ollama_client = AsyncClient(host=OLLAMA_URL, timeout=OLLAMA_TIMEOUT)

collection = create_collection("docs")

user_history = {}

# TOPIC_KEYWORDS = {
#     "стипендия":[
#         "стипенд", "стипуха", "академическ", "социальн", "повышенн",
#         "грант", "матпомощ", "выплат", "денежн поддержк"
#     ],
#     "аспирантура":[
#         "аспиран", "диссертац", "кандидатск", "научн руководител",
#         "вак", "научн исследован", "аспирантур", "кандидат наук",
#         "публикац", "конференц"
#     ],
#     "бакалавриат":[
#         "проходн бал", "егэ", "балл", "поступлен",
#         "абитуриент", "конкурс", "направлени",
#         "прием", "приём", "зачислен", "поступит",
#         "минимальн бал"
#     ],
#     "расписание":["расписан", "знач", "сокращ"]
# }

def clean_json(content: str) -> str:
    if content.startswith("```json"):
        content = content[len("```json"):]
    return content.strip(" \n`")

async def detect_topic(query: str):
    query_lower = query.lower()

    response = await ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": dector_system_input},
            {"role": "user", "content": query_lower}
        ],
        format='json',
        options={"temperature": 0.2}
    )

    content = response["message"]["content"]

    data = json.loads(clean_json(content))

    return data["clear_user_input"], data["topic"], data["major_id"]


async def retrieve(query, n_results=40):
    query, topics, major_id = await detect_topic(query)

    if topics == "swearing" or not query or topics is None:
        return [], [], [], topics, query

    query_embedding = get_embedding([query])

    if major_id:
        major_id = major_id[:8]
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where={
                "$and": [
                    {"topics": topics},
                    {"major_id": major_id}
                ]
            }
        )
    else:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where={"topics": topics}
        )

    return (
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
        topics,
        query
    )

def rerank(query, pairs):
    docs = [chunk for chunk, _ in pairs]
    model_inputs = [(query, doc) for doc in docs]

    scores = reranker.predict(model_inputs)

    ranked = sorted(
        zip(pairs, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return ranked

def get_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Сбросить диалог", callback_data="reset_dialog")],
        [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
        [InlineKeyboardButton(text="📞 Связь с оператором", callback_data="operator")]
    ])

def sanitize_html(text: str) -> str:
    # защищаем < и >
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    
    # возвращаем разрешённые теги обратно
    allowed_tags = ["b", "i", "code", "pre"]
    
    for tag in allowed_tags:
        text = text.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        text = text.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    
    return text

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_history[message.from_user.id] =[]
    welcome_text = (
        "👋 Привет! Я профессиональный ИИ-консультант Московского Политеха.\n\n"
        "Задай мне любой вопрос про расписание, стипендии, бакалавриат или аспирантуру!"
    )
    await message.answer(welcome_text, reply_markup=get_inline_keyboard())

@dp.callback_query(F.data == "reset_dialog")
async def process_reset_dialog(callback: CallbackQuery):
    user_history[callback.from_user.id] =[]
    await callback.message.answer(
        "🔄 Контекст диалога успешно сброшен! Я готов ответить на новые вопросы.",
        reply_markup=get_inline_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "faq")
async def process_faq(callback: CallbackQuery):
    faq_text = (
    "📌 <b>Частые темы обращений:</b>\n\n"
    "🎓 <b>Бакалавриат:</b> проходные баллы, подача документов, направления.\n"
    "💰 <b>Стипендии:</b> виды выплат, как получить повышенную стипендию, матпомощь.\n"
    "📅 <b>Расписание:</b> как узнать расписание, графики сессий.\n"
    "🔬 <b>Аспирантура:</b> поступление, научные руководители.\n\n"
    "Просто напиши свой вопрос в чат!"
    )
    await callback.message.answer(faq_text, parse_mode="HTML", reply_markup=get_inline_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "operator")
async def process_operator(callback: CallbackQuery):
    operator_text = (
    "📞 <b>Горячая линия Московского Политеха:</b>\n"
    "+7 (495) 223-05-23\n\n"
    "📧 <b>Email:</b>\n"
    "mospolytech@mospolytech.ru\n\n"
    "📍 <b>МФЦ Московского Политеха:</b>\n"
    "ул. Большая Семеновская, 38"
    )
    await callback.message.answer(operator_text, parse_mode="HTML", reply_markup=get_inline_keyboard())
    await callback.answer()

@dp.message()
async def handle_user_message(message: Message):
    user_id = message.from_user.id
    user_input = message.text

    if user_id not in user_history:
        user_history[user_id] = []

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        context_chunks, metadatas, distances, topics, clean_query = await retrieve(user_input)

        pairs = list(zip(context_chunks, metadatas))

        if topics == "проходной балл":
            ranked_docs = rerank(clean_query, pairs)
            context_text = "\n".join([
                f"{chunk} | Проходной балл: {meta['passing_budget']} | "
                f"Платка: {meta['passing_paid']} | "
                f"{meta['major_id']} | {str(score)[:4]}"
                for (chunk, meta), score in ranked_docs[:10]
            ])

        elif topics == "swearing" or topics is None:
            context_text = (
                "Пользователь использует неприемлемую лексику. "
                "Игнорируй его ввод и отвечай как бот Политеха."
            )

        else:
            ranked_docs = rerank(clean_query, pairs)
            context_text = "\n".join([
                f"{chunk} | {str(score)[:4]}"
                for (chunk, meta), score in ranked_docs[:10]
            ])

        formatted_system_prompt = system_input.format(
            context_temp=context_text,
            user_input_temp=user_input
        )

        messages = [{"role": "system", "content": formatted_system_prompt}]

        for msg in user_history[user_id][-6:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_input})

        response = await ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"temperature": 0.2}
        )

        raw_answer = response["message"]["content"]
        answer = sanitize_html(raw_answer)

        user_history[user_id].append({"role": "user", "content": user_input})
        user_history[user_id].append({"role": "assistant", "content": raw_answer})

        if len(user_history[user_id]) > 7:
            user_history[user_id] = user_history[user_id][-7:]

        await message.answer(answer, parse_mode="HTML", reply_markup=get_inline_keyboard())

    except Exception as e:
        print("ERROR:", e)
        await message.answer(
            "Ошибка RAG или модели 😔",
            reply_markup=get_inline_keyboard()
        )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())