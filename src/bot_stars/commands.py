### Команды бота
from telegram import KeyboardButton, Update

# from .utils import getRepository
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)
from datetime import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update

from bot_stars.utils import getSheetRepository

NAME, LASTNAME, BIRTHDATE, PHONE = range(4)


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Запоминаем id пользователя
    user_id = update.message.from_user.id
    context.user_data["user_id"] = user_id

    keyboard = [["Отменить"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )

    # name?
    sent_message = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Как тебя зовут?",
        reply_markup=reply_markup,
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
            message_id=context.user_data["last_bot_message_id"],
        )
    context.user_data["user_name"] = user_name

    keyboard = [["Отменить"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    # lastname?
    sent_message = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Напиши свою фамилию?",
        reply_markup=reply_markup,
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
            message_id=context.user_data["last_bot_message_id"],
        )

    context.user_data["user_lastname"] = user_lastname

    keyboard = [["Отменить"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )

    # birthdate?
    sent_message = await context.bot.send_message(
        chat_id=update.message.chat.id,
        text=f"Когда твой день рождения? (в формате ДД.ММ.ГГГГ)",
        reply_markup=reply_markup,
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
            message_id=context.user_data["last_bot_message_id"],
        )

    try:
        birthdate = datetime.strptime(birthdate_str, "%d.%m.%Y")

        # check
        today = datetime.today()
        age = (
            today.year
            - birthdate.year
            - ((today.month, today.day) < (birthdate.month, birthdate.day))
        )

        if age > 50:
            await update.message.reply_text(
                "Кажется, ты ввел неверную дату. Пожалуйста, повтори ввод (формат ДД.ММ.ГГГГ)."
            )
            return BIRTHDATE

        context.user_data["birthdate"] = birthdate_str

        keyboard = [[KeyboardButton("📱 Отправить номер", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(
            "Отлично! Теперь отправь свой номер телефона:", reply_markup=reply_markup
        )

        return PHONE

    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты. Пожалуйста, введи дату в формате ДД.ММ.ГГГГ."
        )
        return BIRTHDATE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = (
        update.message.contact.phone_number
        if update.message.contact
        else update.message.text
    )

    # Выводим финальное сообщение
    user_id = context.user_data["user_id"]
    user_name = context.user_data["user_name"]
    user_lastname = context.user_data["user_lastname"]
    birthdate_str = context.user_data["birthdate"]
    phone = context.user_data["phone"]

    getSheetRepository(context).saveNewUser(
        user_id, user_name, user_lastname, birthdate_str, phone
    )
    await update.message.reply_text(
        f"Спасибо! Ты успешно зарегистрирован.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data["in_dialog"] = False

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Регистрация остановлена, для продолжения используйте /start.",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data["in_dialog"] = False
    return ConversationHandler.END
