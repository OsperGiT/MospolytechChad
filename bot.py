import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import os
from utils.pipeline import init_rag_services 

# Инициализация
rag_sys = init_rag_services()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

# История сообщений пользователя
user_history = {}

# Кнопки взаимодействия
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сбросить диалог", callback_data="reset_dialog")],
        [InlineKeyboardButton(text="📞 Оператор", callback_data="operator")]
    ])

# Хендлеры
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_history[user_id] = []
    await message.answer(
        "👋 Привет! Я ИИ-консультант Московского Политеха.\nЗадай мне любой вопрос!",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "reset_dialog")
async def process_reset(callback: CallbackQuery):
    user_history[callback.from_user.id] = []
    await callback.message.answer("🔄 История очищена. Начнем с чистого листа!")
    await callback.answer()

@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_input = message.text

    # Создаем память для нового пользователя
    if user_id not in user_history:
        user_history[user_id] = []

    # Визуальный эффект "Печатает..."
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        response = await rag_sys.get_answer(
            user_input, 
            user_history=user_history[user_id], 
            stream=False
        )

        # Обновляем историю
        user_history[user_id] = rag_sys.create_history(user_history[user_id], user_input, response["message"]["content"])

        await message.answer(response["message"]["content"], reply_markup=get_main_keyboard())

    except Exception as e:
        logging.error(f"Ошибка RAG: {e}")
        await message.answer("⚠️ Произошла ошибка при генерации ответа.")

async def main():
    print("🤖 Бот запущен через RAGEngine...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")