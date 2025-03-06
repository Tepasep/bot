import os
from dotenv import load_dotenv

from bot_stars.repository import SheetsRepository

from .commands import start
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    Application,
    MessageHandler,
)
from .commands import (
    start,
    get_name,
    get_birthdate,
    get_lastname,
    NAME,
    BIRTHDATE,
    LASTNAME,
    cancel,
)


def main():
    ### Инициализация переменных окружения
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")

    if not TOKEN or not SPREADSHEET_NAME:
        raise ValueError("Не заданы TELEGRAM_BOT_TOKEN или SPREADSHEET_NAME")

    ### Инициализация репозитория
    sheet_repository = SheetsRepository("./credentials.json", SPREADSHEET_NAME)
    #    repository = Repository(DB_TOKEN)

    # Создание приложения
    app = Application.builder().token(TOKEN).build()

    # Сохранение repository в bot_data
    app.bot_data["sheet_repository"] = sheet_repository
    #    app.bot_data["repository"] = repository

    # start

    # ConversationHandler для управления диалогом
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],  # Указываем команду /start как точку входа
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
