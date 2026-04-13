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
from .keyboards import BTN_HELP, BTN_ASK, BTN_ADMIN_ADDSTARS, BTN_ADMIN_REMSTARS
from .commands import (
    handle_menu,
    cancel_current_action_and_dispatch_menu,
    MENU_BUTTON_TEXTS,
    send_help_message,
    start,
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
    list_users,
    show_user_stars,
    handle_confirmation,
    handle_user_selection_block,
    handle_confirmation1,
    handle_user_selection_unblock,
    GENDER,
    get_gender,
    top,
    handle_user_question,
    handle_admin_actions,
    active_questions,
    handle_answer,
    ANSWER_INPUT,
    start_question_flow,
    stars_add,
    stars_remove,
    SELECT_TEEN,
    ENTER_COMMENT,
    ENTER_STARS,
    PREVIEW_MESSAGE,
    stars_cancel_operation,
    stars_handle_teen_selection,
    stars_enter_amount,
    stars_enter_comment,
    stars_preview_action,
    HANDLING_QUESTION,
)
from .health import start_health_server


warnings.filterwarnings("ignore", category=PTBUserWarning)


def main():
    load_dotenv()
    # Запуск HTTP healthcheck сервера в фоне как можно раньше
    HEALTH_PORT = int(os.getenv("HEALTHCHECK_PORT", "8000"))
    start_health_server(port=HEALTH_PORT)

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

    menu_button_filter = filters.Text(list(MENU_BUTTON_TEXTS))
    text_without_menu_filter = filters.TEXT & ~filters.COMMAND & ~menu_button_filter
    
    # ConversationHandler для работы со звездами
    stars_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text([BTN_ADMIN_ADDSTARS]), stars_add),
            MessageHandler(filters.Text([BTN_ADMIN_REMSTARS]), stars_remove),
        ],
        states={
            SELECT_TEEN: [
                CallbackQueryHandler(stars_handle_teen_selection, pattern="^stars_select_teen_"),
                CallbackQueryHandler(stars_cancel_operation, pattern="^stars_cancel_operation$")
            ],
            ENTER_STARS: [MessageHandler(text_without_menu_filter, stars_enter_amount)],
            ENTER_COMMENT: [MessageHandler(text_without_menu_filter, stars_enter_comment)],
            PREVIEW_MESSAGE: [
                CallbackQueryHandler(stars_preview_action, pattern="^stars_confirm_send$"),
                CallbackQueryHandler(stars_preview_action, pattern="^stars_edit_comment$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(stars_cancel_operation, pattern="^stars_cancel_operation$"),
            MessageHandler(menu_button_filter, cancel_current_action_and_dispatch_menu),
        ],
    )

    #Вопросы
    app.add_handler(ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text([BTN_ASK]), start_question_flow),
            CommandHandler('active_questions', active_questions),
            CallbackQueryHandler(handle_admin_actions, pattern="^(answer_|reject_|select_)")
        ],
        states={
            HANDLING_QUESTION: [MessageHandler(text_without_menu_filter, handle_user_question)],
            ANSWER_INPUT: [MessageHandler(text_without_menu_filter, handle_answer)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            MessageHandler(menu_button_filter, cancel_current_action_and_dispatch_menu),
        ]
    ))
    
    # ConversationHandler для /start
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(text_without_menu_filter, get_name)],
            LASTNAME: [MessageHandler(text_without_menu_filter, get_lastname)],
            BIRTHDATE: [MessageHandler(text_without_menu_filter, get_birthdate)],
            GENDER: [MessageHandler(text_without_menu_filter, get_gender)],
            PHONE: [
                MessageHandler(
                    filters.CONTACT | text_without_menu_filter, get_phone
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(menu_button_filter, cancel_current_action_and_dispatch_menu),
        ],
    )

    app.add_handler(stars_conv_handler)

    # block
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CallbackQueryHandler(handle_user_selection_block, pattern="^block_user_"))
    app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^confirm_block_"))
    app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^cancel_block$"))
    # unblock
    app.add_handler(CommandHandler("unblock", unblock_user))
    app.add_handler(CallbackQueryHandler(handle_user_selection_unblock, pattern="^unblock_user_"))
    app.add_handler(CallbackQueryHandler(handle_confirmation1, pattern="^confirm_unblock_"))
    app.add_handler(CallbackQueryHandler(handle_confirmation1, pattern="^cancel_unblock$"))
    # другое
    app.add_handler(CommandHandler("list", list_users))
    app.add_handler(CallbackQueryHandler(show_user_stars, pattern="^user_stars_"))
    
    app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="^answer_"))
    app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="^reject_"))
    app.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="^select_"))
    
    app.add_handler(CommandHandler("help", send_help_message))
    app.add_handler(CommandHandler("viewstars", viewstars))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.run_polling()


if __name__ == "__main__":
    main()
