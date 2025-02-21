import os
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv
from .repository import Repository
from .commands import start

def main():
    ### Инициализация переменных окружения
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DB_TOKEN = os.getenv("DB_TOKEN")
    
    if not TOKEN or not DB_TOKEN:
        raise ValueError("Не заданы TELEGRAM_BOT_TOKEN или DB_TOKEN")
    
    ### Инициализация репозитория
    repository = Repository(DB_TOKEN)
    
    # Создание приложения
    app = Application.builder().token(TOKEN).build()
    
    # Сохранение repository в bot_data
    app.bot_data["repository"] = repository  

    # Добавление команд
    app.add_handler(CommandHandler("start", start))

    # Запуск бота
    app.run_polling()

if __name__ == "__main__":
    main()