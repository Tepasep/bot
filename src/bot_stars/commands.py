### Команды бота
from telegram import Update
from telegram.ext import ContextTypes
from .utils import getRepository


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    repository = getRepository(context)
    users = repository.findUsersById(user_id)

    if len(users) == 0:
        user_id = update.message.from_user.id  # Получаем ID пользователя
        first_name = update.message.from_user.first_name  # Имя пользователя
        last_name = update.message.from_user.last_name  # Фамилия пользователя
        chat_id = update.message.chat_id

        repository.createUser(user_id, first_name, last_name, chat_id)

        await update.message.reply_text("Привет! Давай знакомиться. Как тебя зовут?")
    else:
        if users[0].data.get("chat_id") != chat_id:
            repository.updateChatId(user_id, chat_id)

        await update.message.reply_text(
            "Привет! Используй /viewstars для просмотра звёзд."
        )
