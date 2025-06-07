import os
import warnings
from dotenv import load_dotenv

from bot_stars.repository import SheetsRepository

from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    Application,
    CallbackQueryHandler,
)
from telegram.warnings import PTBUserWarning
from .keyboards import BTN_HELP
from .commands import (
    handle_menu,
    start,
    enter_stars,
    get_phone,
    get_name,
    get_birthdate,
    get_lastname,
    PHONE,
    NAME,
    BIRTHDATE,
    LASTNAME,
    cancel,
    block_user,
    unblock_user,
    viewstars,
    select_teen,
    SELECT_TEEN,
    ENTER_STARS,
    ENTER_COMMENT,
    stop,
    handle_teen_selection,
    cancel_conversation,
    list_users,
    show_user_stars,
    handle_confirmation,
    handle_user_selection_block,
    handle_confirmation1,
    handle_user_selection_unblock,
    enter_comment,
    GENDER,
    get_gender,
    top,
    handle_user_question,
    handle_admin_actions,
    active_questions,
    handle_answer,
    ANSWER_INPUT,
    start_question_flow,
    remove_keyboard,
)


warnings.filterwarnings("ignore", category=PTBUserWarning)


def main():
    ### Инициализация переменных окружения
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
    CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

    if not CREDENTIALS_FILE:
        raise ValueError("Не задан CREDENTIALS_FILE")
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"Файл {CREDENTIALS_FILE} не найден")
    if not TOKEN or not SPREADSHEET_NAME:
        raise ValueError("Не заданы TELEGRAM_BOT_TOKEN или SPREADSHEET_NAME")

    # Инициализация репозитория
    sheet_repository = SheetsRepository(CREDENTIALS_FILE, SPREADSHEET_NAME)

    # Создание приложения
    app = Application.builder().token(TOKEN).build()

    # Сохранение repository в bot_data
    app.bot_data["sheet_repository"] = sheet_repository
    
    #Вопросы
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Text([BTN_HELP]), start_question_flow)],
        states={
            "HANDLING_QUESTION": [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_question)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        ))
    
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('active_questions', active_questions),
                     CallbackQueryHandler(handle_admin_actions)],
        states={
            ANSWER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        ))
    
    app.add_handler(CallbackQueryHandler(handle_admin_actions))

    # ConversationHandler для /start
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lastname)],
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birthdate)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            PHONE: [
                MessageHandler(
                    filters.CONTACT | (filters.TEXT & ~filters.COMMAND), get_phone
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    def createMoveStarsHandler(command: str, operation: str):
        return ConversationHandler(
            entry_points=[CommandHandler(command, select_teen)],
            states={
                SELECT_TEEN: [
                    CallbackQueryHandler(
                        handle_teen_selection, pattern="^select_teen_"
                    ),
                    CallbackQueryHandler(cancel_conversation, pattern="cancel"),
                ],
                ENTER_STARS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_stars),
                    CallbackQueryHandler(cancel_conversation, pattern="cancel"),
                ],
                ENTER_COMMENT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, enter_comment(operation)
                    ),
                    CallbackQueryHandler(cancel_conversation, pattern="cancel"),
                ],
            },
            fallbacks=[CommandHandler("cancel", stop)],
            per_chat=True,
            per_user=True,
            per_message=False,
        )


    # Handler для /addstars и /remstars
    add_stars_handler = createMoveStarsHandler("addstars", "add")
    rem_stars_handler = createMoveStarsHandler("remstars", "rem")
    #обработчики 
    app.add_handler(add_stars_handler)
    app.add_handler(rem_stars_handler)

    # block
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(
        CallbackQueryHandler(handle_user_selection_block, pattern="^block_user_")
    )
    app.add_handler(
        CallbackQueryHandler(handle_confirmation, pattern="^confirm_block_")
    )
    app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^cancel_block$"))
    # unblock
    app.add_handler(CommandHandler("unblock", unblock_user))
    app.add_handler(
        CallbackQueryHandler(handle_user_selection_unblock, pattern="^unblock_user_")
    )
    app.add_handler(
        CallbackQueryHandler(handle_confirmation1, pattern="^confirm_unblock_")
    )
    app.add_handler(
        CallbackQueryHandler(handle_confirmation1, pattern="^cancel_unblock$")
    )
    # другое
    app.add_handler(CommandHandler("list", list_users))
    app.add_handler(CallbackQueryHandler(show_user_stars, pattern="^user_stars_"))
    app.add_handler(add_stars_handler)
    app.add_handler(rem_stars_handler)
    app.add_handler(CommandHandler("viewstars", viewstars))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.run_polling()


if __name__ == "__main__":
    main()
