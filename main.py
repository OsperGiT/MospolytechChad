from utils.pipeline import init_rag_services
import asyncio

async def main():
    # Инициализирует зависимости
    rag_sys = init_rag_services()
    print("Чат с ботом запущен, напишите 'exit', чтобы выйти")
    user_input = ""
    user_id = 1
    user_history = {user_id: []}

    while True:
        
        user_input = await asyncio.to_thread(input, "Вы: ")
        if user_input == "exit":
            break
        
        response = ""
        stream = await rag_sys.get_answer(user_input, user_history[user_id], stream = True)
        async for content in stream:
            response += content.message.content
            print(content.message.content, end="", flush=True)
        print()
        
        user_history[user_id] = rag_sys.create_history(user_history[user_id], user_input, response)
        print(f"История сообщений: {user_history[user_id]}")

if __name__ == "__main__":
    try:
        asyncio.run(main()) 
    except KeyboardInterrupt:
        print("Бот остановлен.")