### Команды бота
from telegram import Update
# from .utils import getRepository
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext, ContextTypes
from datetime import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update

NAME, LASTNAME, BIRTHDATE = range(3)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Запоминаем id пользователя
    user_id = update.message.from_user.id
    context.user_data['user_id'] = user_id

    keyboard = [["Отменить"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    # name?
    sent_message = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Как тебя зовут?",
        reply_markup=reply_markup
    )

    context.user_data["last_bot_message_id"] = sent_message.message_id
    context.user_data["in_dialog"] = True
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text
    if user_name == "Отменить":
        return await cancel(update, context)
    if "last_bot_message_id" in context.user_data:
        await context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=context.user_data["last_bot_message_id"]
        )
    context.user_data['user_name'] = user_name
    
    keyboard = [["Отменить"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    # lastname?
    sent_message = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Напиши свою фамилию?",
        reply_markup=reply_markup
    )
    context.user_data["last_bot_message_id"] = sent_message.message_id
    return LASTNAME

async def get_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_lastname = update.message.text
    if user_lastname == "Отменить":
        return await cancel(update, context)
    if "last_bot_message_id" in context.user_data:
        await context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=context.user_data["last_bot_message_id"]
        )
    
    context.user_data['user_lastname'] = user_lastname
    
    keyboard = [["Отменить"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    # birthdate?
    sent_message = await context.bot.send_message(
        chat_id=update.message.chat.id,
        text=f"Когда твой день рождения? (в формате ДД.ММ.ГГГГ)",
        reply_markup=reply_markup
    )

    context.user_data["last_bot_message_id"] = sent_message.message_id

    return BIRTHDATE

async def get_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    birthdate_str = update.message.text
    if birthdate_str == "Отменить":
        return await cancel(update, context)
    if "last_bot_message_id" in context.user_data:
        await context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=context.user_data["last_bot_message_id"]
        )
    
    try:
        birthdate = datetime.strptime(birthdate_str, "%d.%m.%Y")
        
        # check
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        
        if age > 50:
            await update.message.reply_text("Кажется, ты ввел неверную дату. Пожалуйста, повтори ввод (формат ДД.ММ.ГГГГ).")
            return BIRTHDATE
        
        context.user_data['birthdate'] = birthdate_str
        
        # Выводим финальное сообщение
        user_id = context.user_data['user_id']
        user_name = context.user_data['user_name']
        user_lastname = context.user_data['user_lastname']
        await update.message.reply_text(
            f"Твой ID: {user_id}, имя: {user_name}, фамилия: {user_lastname}, день рождения: {birthdate_str}.",
            reply_markup=ReplyKeyboardRemove() 
        )
        context.user_data["in_dialog"] = False
        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Пожалуйста, введи дату в формате ДД.ММ.ГГГГ.")
        return BIRTHDATE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Регистрация остановлена, для продолжения используйте /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    context.user_data["in_dialog"] = False
    return ConversationHandler.END