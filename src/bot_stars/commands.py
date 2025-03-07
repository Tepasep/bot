### Команды бота
from telegram import KeyboardButton, Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import os
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler
)
from datetime import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from datetime import datetime
from bot_stars.utils import getSheetRepository

NAME, LASTNAME, BIRTHDATE, PHONE = range(4)
SELECT_USER, ENTER_STARS = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Запоминаем id пользователя
    user_id = update.message.from_user.id
    sheet_repo = getSheetRepository(context)

    # Проверяем, заблокирован ли пользователь
    access_status = sheet_repo.getUserAccess(user_id)
    if access_status and "Запрет" in access_status:
        await update.message.reply_text("Нет доступа. Напиши @pulatovman")
        return ConversationHandler.END

    # Проверяем, зарегистрирован ли пользователь
    if sheet_repo.sheet.find(str(user_id)):
        await update.message.reply_text("Используй /viewstars")
        return ConversationHandler.END
    
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

async def viewstars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    sheet_repo = getSheetRepository(context)
    # Проверяем, заблокирован ли пользователь
    access_status = sheet_repo.getUserAccess(user_id)
    if access_status and "Запрет" in access_status:
        await update.message.reply_text("Нет доступа. Напиши @pulatovman")
        return ConversationHandler.END

    sheet_repo = getSheetRepository(context)

    cell = sheet_repo.sheet.find(str(user_id))
    if not cell:
        await update.message.reply_text("Вы не зарегистрированы. Используйте /start.")
        return

    # Здесь можно добавить логику для отображения данных пользователя
    await update.message.reply_text("Пока пусто...")

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

    # Удаление предыдущего сообщения бота
    if "last_bot_message_id" in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=context.user_data["last_bot_message_id"],
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")  # Логируем ошибку, но продолжаем выполнение

    try:
        birthdate = datetime.strptime(birthdate_str, "%d.%m.%Y")
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        if age > 50:
            sent_message = await update.message.reply_text("Кажется, ты ввел неверную дату. Пожалуйста, повтори ввод (формат ДД.ММ.ГГГГ).")
            context.user_data["last_bot_message_id"] = sent_message.message_id  # Сохраняем message_id
            return BIRTHDATE

        context.user_data["birthdate"] = birthdate_str

        keyboard = [[KeyboardButton("📱 Отправить номер", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        sent_message = await update.message.reply_text("Отлично! Теперь отправь свой номер телефона:", reply_markup=reply_markup)
        context.user_data["last_bot_message_id"] = sent_message.message_id  # Сохраняем message_id

        return PHONE

    except ValueError:
        sent_message = await update.message.reply_text("Неверный формат даты. Пожалуйста, введи дату в формате ДД.ММ.ГГГГ.")
        context.user_data["last_bot_message_id"] = sent_message.message_id  # Сохраняем message_id
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
    context.user_data.clear()
    context.user_data["in_dialog"] = False

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Регистрация остановлена, для продолжения используйте /start.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    context.user_data["in_dialog"] = False
    return ConversationHandler.END


async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id

    if user_id not in admin_ids:
        return

    if not context.args:
        await update.message.reply_text("Использование: /block <user_id>")
        return

    target_user_id = context.args[0]
    try:
        target_user_id = int(target_user_id)
    except ValueError:
        await update.message.reply_text("Некорректный ID пользователя.")
        return

    getSheetRepository(context).blockUser(target_user_id)
    await update.message.reply_text(f"Пользователь {target_user_id} заблокирован.")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id

    if user_id not in admin_ids:
        return

    if not context.args:
        await update.message.reply_text("Использование: /unblock <user_id>")
        return

    target_user_id = context.args[0]
    try:
        target_user_id = int(target_user_id)
    except ValueError:
        await update.message.reply_text("Некорректный ID пользователя.")
        return

    getSheetRepository(context).unblockUser(target_user_id)
    await update.message.reply_text(f"Пользователь {target_user_id} разблокирован.")

# Добавление звёзд
async def add_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id
    if user_id not in admin_ids:
        return
    
    sheet_repo = getSheetRepository(context)

    # Получаем все данные из таблицы
    try:
        data = sheet_repo.sheet.get_all_values()  # Получаем все строки таблицы
    except Exception as e:
        await update.message.reply_text(f"Ошибка при чтении данных из таблицы: {e}")
        return

    # Создаем inline-кнопки с именами и фамилиями пользователей
    keyboard = []
    for row in data[1:]:  # Пропускаем первую строку (заголовки)
        user_id_col = row[0]
        name = row[1]
        lastname = row[2]
        if name and lastname and user_id_col:
            # Создаем кнопку с именем и фамилией
            button = InlineKeyboardButton(
                text=f"{name} {lastname}",
                callback_data=f"select_user_{user_id_col}"  # Передаем ID пользователя в callback_data
            )
            keyboard.append([button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите пользователя:",
        reply_markup=reply_markup
    )
    return SELECT_USER

async def select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_user = update.message.text

    if selected_user == "Отмена":
        await stop(update, context) 
        return ConversationHandler.END

    context.user_data["selected_user"] = selected_user

    await update.message.reply_text("Введите количество звёзд:", reply_markup=ReplyKeyboardRemove())

    return ENTER_STARS

async def enter_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stars = update.message.text

    try:
        stars = int(stars)
    except ValueError:
        await update.message.reply_text("Некорректное количество звёзд. Введите число.")
        return ENTER_STARS

    selected_user_id = context.user_data.get("selected_user_id")

    sheet_repo = getSheetRepository(context)

    # Получаем все данные из таблицы
    try:
        data = sheet_repo.sheet.get_all_values()  # Получаем все строки таблицы
    except Exception as e:
        await update.message.reply_text(f"Ошибка при чтении данных из таблицы: {e}")
        return

    # Ищем строку с выбранным пользователем
    for i, row in enumerate(data):
        if row[0] == selected_user_id:  # Ищем по ID пользователя (колонка A)
            # Получаем текущее количество звёзд из колонки L (индекс 6, так как индексация с 0)
            current_stars = row[6] if len(row) > 6 else "0"
            current_stars = int(current_stars) if current_stars else 0

            new_stars = current_stars + stars
            sheet_repo.sheet.update_cell(i + 1, 7, str(new_stars))  # i + 1, так как строки нумеруются с 1

            await update.message.reply_text(f"Добавлено {stars} звёзд пользователю {row[1]} {row[2]}. Теперь у него {new_stars} звёзд.")
            return ConversationHandler.END

    await update.message.reply_text("Пользователь не найден.")
    return ConversationHandler.END

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Регистрация остановлена, для продолжения используйте /start.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    user_id = callback_data.split("_")[-1]
    context.user_data["selected_user_id"] = user_id
    cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel_stars_input")
    reply_markup = InlineKeyboardMarkup([[cancel_button]])
    await query.edit_message_text(
        "Введите количество звёзд:",
        reply_markup=reply_markup
    )
    return ENTER_STARS

async def cancel_stars_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    await query.edit_message_text("Действие отменено.")
    return ConversationHandler.END