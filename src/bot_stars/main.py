import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

from .services.user_service import UserService


load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = [os.getenv("ADMIN_ID")]  # ID админа

user_service = UserService()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Используй /admin для управления или /viewstars для просмотра звёзд.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_ID:
        return await update.message.reply_text("У вас нет прав.")

    await update.message.reply_text(
        "/adduser - Добавить пользователя\n"
        "/addstars - Начислить звёзды"
    )

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_ID:
        return await update.message.reply_text("Нет прав.")

    args = context.args
    if len(args) < 5:
        return await update.message.reply_text("Использование: /adduser Имя Фамилия ID Телефон ДР")

    name, surname, chatID, telephone, dr = args
    message = user_service.add_user(name, surname, chatID, telephone, dr)
    await update.message.reply_text(message)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("adduser", add_user))
    app.run_polling()

if __name__ == "__main__":
    main()