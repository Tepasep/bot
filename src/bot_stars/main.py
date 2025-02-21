import os
from dotenv import load_dotenv
#from .repository import Repository
from .commands import start
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext, Application, CallbackQueryHandler, MessageHandler
from datetime import datetime
from .commands import start, get_name, get_birthdate, get_lastname, NAME, BIRTHDATE, LASTNAME, cancel

def main():
    ### Инициализация переменных окружения
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DB_TOKEN = os.getenv("DB_TOKEN")
    
    if not TOKEN or not DB_TOKEN:
        raise ValueError("Не заданы TELEGRAM_BOT_TOKEN или DB_TOKEN")
    
    ### Инициализация репозитория
#    repository = Repository(DB_TOKEN)
    
    # Создание приложения
    app = Application.builder().token(TOKEN).build()
    
    # Сохранение repository в bot_data
#    app.bot_data["repository"] = repository  

    #start

        # ConversationHandler для управления диалогом
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],  # Указываем команду /start как точку входа
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],  
            LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lastname)], 
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birthdate)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],  # Обработка команды /cancel
    )

    # Регистрируем ConversationHandler
    app.add_handler(conv_handler)


    # Добавление команд
    """app.add_handler(CommandHandler("start", start))  -  как пример, но она нам больше не нужна"""

    # Запуск бота
    app.run_polling()

if __name__ == "__main__":
    main()