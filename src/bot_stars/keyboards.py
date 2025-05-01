from telegram import ReplyKeyboardMarkup

# Тексты кнопок как константы
BTN_BALANCE = "💫 Мой баланс"
BTN_HELP = "📨 Помощь"
BTN_ASK = "❓ Задать вопрос"
BTN_TOP = "🏆 Топ"


# Главная клавиатура
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [[BTN_BALANCE], [BTN_TOP, BTN_HELP]], resize_keyboard=True, one_time_keyboard=False
)


# Административная клавиатура
BTN_ADMIN_LIST = "👥 Список пользователей"
BTN_ADMIN_ADDSTARS = "⭐️ Добавить звезды"
BTN_ADMIN_REMSTARS = "⭐️ Убрать звезды"
BTN_ADMIN_BLOCK = "🚫 Заблокировать пользователя"
BTN_ADMIN_UNBLOCK = "🚫 Разблокировать пользователя"
BTN_ADMIN_QUESTIONS = "📝 Активные вопросы"


ADMIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        [BTN_BALANCE, BTN_ADMIN_QUESTIONS],
        [BTN_TOP, BTN_ADMIN_LIST],
        [BTN_ADMIN_ADDSTARS, BTN_ADMIN_REMSTARS],
        [BTN_ADMIN_BLOCK, BTN_ADMIN_UNBLOCK],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)
