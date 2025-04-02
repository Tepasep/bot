from telegram import (
    KeyboardButton,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import os
from telegram.ext import ConversationHandler, ContextTypes, CallbackQueryHandler
from datetime import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from datetime import datetime
from bot_stars.utils import getSheetRepository
import random

# morph = pymorphy2.MorphAnalyzer()

NAME, LASTNAME, BIRTHDATE, GENDER, PHONE = range(5)
SELECT_TEEN, ENTER_STARS, ENTER_COMMENT = range(3)


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
    if sheet_repo.sheet1.find(str(user_id)):
        admin_ids_str = os.getenv("ADMIN_ID")
        admin_ids_str = admin_ids_str.replace('"', "").replace("'", "")
        admin_ids = [int(id.strip()) for id in admin_ids_str.split(",")]
        user_id = update.message.from_user.id

        if user_id in admin_ids:
            await update.message.reply_text(
                f"Ты администратор, команды для тебя: \n**1.** /list \n**2.** /addstars \n**3.** /remstars \n**4.** /block \n**5.** /unblock \n**6.** /viewstars",
                parse_mode="Markdown",
            )
            return
        
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
    access_status = sheet_repo.getUserAccess(user_id)
    if access_status and "Запрет" in access_status:
        await update.message.reply_text("Нет доступа. Напиши @pulatovman")
        return ConversationHandler.END

    cell = sheet_repo.sheet1.find(str(user_id))
    if not cell:
        await update.message.reply_text("Вы не зарегистрированы. Используйте /start.")
        return
    data = sheet_repo.sheet1.get_all_values()
    stars = "0"
    for row in data[1:]:
        if len(row) > 6 and row[0] == str(user_id):
            stars = row[6] if row[6] else "0"
            break

    comments = sheet_repo.get_last_comments(int(user_id), limit=10)
    comments = comments[::-1]

    message = f"Ваше количество звёзд: {stars}\n\nПоследние операции:\n"
    for comment in comments:
        operation_type = comment[1]  # Колонка "Тип операции"
        stars = int(comment[2])  # Колонка "Звёзды"
        comment_text = comment[3]  # Колонка "Комментарий"
        datetime = comment[4]  # Колонка "Дата и время"
        dec_stars = await decline_stars_message(stars)
        message += (
            f"{operation_type} {stars} {dec_stars}: {comment_text} ({datetime})\n"
        )

    await update.message.reply_text(message)


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
            print(f"Не удалось удалить сообщение: {e}")

    try:
        birthdate = datetime.strptime(birthdate_str, "%d.%m.%Y")
        today = datetime.today()
        age = (
            today.year
            - birthdate.year
            - ((today.month, today.day) < (birthdate.month, birthdate.day))
        )

        if age > 50:
            sent_message = await update.message.reply_text(
                "Кажется, ты ввел неверную дату. Пожалуйста, повтори ввод (формат ДД.ММ.ГГГГ)."
            )
            context.user_data["last_bot_message_id"] = sent_message.message_id
            return BIRTHDATE

        context.user_data["birthdate"] = birthdate_str

        # Создаем клавиатуру для выбора пола
        reply_keyboard = [["Мужской", "Женский"]]
        sent_message = await update.message.reply_text(
            "Выберите ваш пол:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, 
                resize_keyboard=True,
                one_time_keyboard=True
            ),
        )
        context.user_data["last_bot_message_id"] = sent_message.message_id
        return GENDER

    except ValueError:
        sent_message = await update.message.reply_text(
            "Неверный формат даты. Пожалуйста, введи дату в формате ДД.ММ.ГГГГ."
        )
        context.user_data["last_bot_message_id"] = sent_message.message_id
        return BIRTHDATE

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    gender_str = update.message.text
    if gender_str == "Отменить":
        return await cancel(update, context)
    
    if gender_str not in ["Мужской", "Женский"]:  # Исправлено здесь
        sent_message = await update.message.reply_text(
            "Пожалуйста, выберите пол, используя кнопки ниже."
        )
        context.user_data["last_bot_message_id"] = sent_message.message_id
        return GENDER

    if "last_bot_message_id" in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=context.user_data["last_bot_message_id"],
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")

    context.user_data["gender"] = gender_str

    # Запрашиваем номер телефона
    keyboard = [[KeyboardButton("📱 Отправить номер", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    sent_message = await update.message.reply_text(
        "Отлично! Теперь отправь свой номер телефона:", 
        reply_markup=reply_markup
    )
    context.user_data["last_bot_message_id"] = sent_message.message_id
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Получаем список админов
    admin_ids_str = os.getenv("ADMIN_ID")
    admin_ids_str = admin_ids_str.replace('"', "").replace("'", "")
    admin_ids = [int(id.strip()) for id in admin_ids_str.split(",")]
    user_id = update.message.from_user.id

    # Получаем номер телефона
    phone_number = (
        update.message.contact.phone_number if update.message.contact else update.message.text
    )
    context.user_data["phone"] = phone_number

    # Сохраняем все данные пользователя
    user_id = context.user_data["user_id"]
    user_name = context.user_data["user_name"]
    user_lastname = context.user_data["user_lastname"]
    birthdate_str = context.user_data["birthdate"]
    gender = context.user_data["gender"]
    phone = context.user_data["phone"]

    # Сохраняем в репозиторий
    getSheetRepository(context).saveNewUser(
        user_id, user_name, user_lastname, birthdate_str, phone, gender
    )

    if gender == "Мужской":
        if user_id in admin_ids:
            await update.message.reply_text(f"Ты успешно зарегистрирован, команды для тебя: \n**1.** /list \n**2.** /addstars \n**3.** /remstars \n**4.** /block \n**5.** /unblock \n**6.** /viewstars" ,parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text(f"Ты успешно зарегистрирован, для просмотра звёзд используй /viewstars",parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    elif gender == "Женский":
        if user_id in admin_ids:
            await update.message.reply_text(f"Ты успешно зарегистрирована, команды для тебя: \n**1.** /list \n**2.** /addstars \n**3.** /remstars \n**4.** /block \n**5.** /unblock \n**6.** /viewstars",parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text(f"Ты успешно зарегистрирована, для просмотра звёзд используй /viewstars",parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    
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


# Выбор подростка из списка
async def select_teen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id
    if user_id not in admin_ids:
        return

    sheet_repo = getSheetRepository(context)

    try:
        data = sheet_repo.sheet1.get_all_values()
    except Exception as e:
        await update.message.reply_text(f"Ошибка при чтении данных из таблицы: {e}")
        return

    keyboard = []
    for row in data[1:]:
        user_id_col = row[0]
        name = row[1]
        lastname = row[2]
        if name and lastname and user_id_col:
            button = InlineKeyboardButton(
                text=f"{name} {lastname}", callback_data=f"select_teen_{user_id_col}"
            )
            keyboard.append([button])

    cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel")
    keyboard.append([cancel_button])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите подростка:", reply_markup=reply_markup)
    return SELECT_TEEN


async def select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_user = update.message.text

    if selected_user == "Отмена":
        await stop(update, context)
        return ConversationHandler.END

    context.user_data["selected_user"] = selected_user

    await update.message.reply_text(
        "Введите количество звёзд:", reply_markup=ReplyKeyboardRemove()
    )

    return ENTER_STARS


async def enter_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stars = update.message.text
    query = update.callback_query

    try:
        stars = int(stars)
        if stars < 0:
            await update.message.reply_text(
                "Количество звёзд не может быть отрицательным."
            )
            return ENTER_STARS
    except ValueError:
        await update.message.reply_text("Некорректное количество звёзд. Введите число.")
        return ENTER_STARS

    context.user_data["stars"] = stars

    cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel")
    reply_markup = InlineKeyboardMarkup([[cancel_button]])
    # Запрашиваем комментарий
    await update.message.reply_text(
        "Введите комментарий в виде действия в прошедшем времени. Например: помыл посуду, рассказал свидетельство на сцене итп:",
        reply_markup=reply_markup,
    )
    return ENTER_COMMENT


def enter_comment(operation: str):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

        comment = update.message.text.lower()
        stars = int(context.user_data["stars"])
        selected_user_id = context.user_data.get("selected_user_id")
        sheet_repo = getSheetRepository(context)
        COLUMN_ID = 0
        COLUMN_NAME = 1
        COLUMN_LASTNAME = 2
        COLUMN_STARS = 6
        try:
            data = sheet_repo.sheet1.get_all_values()
        except Exception as e:
            await update.message.reply_text(f"Ошибка при чтении данных из таблицы: {e}")
            return

        for i, row in enumerate(data):
            if row[COLUMN_ID] == selected_user_id:
                current_stars = row[COLUMN_STARS] if len(row) > COLUMN_STARS else "0"
                current_stars = int(current_stars) if current_stars else 0

                if operation == "add":
                    new_stars = current_stars + stars
                else:
                    if current_stars - stars < 0:
                        await update.message.reply_text(
                            f"Недостаточно звёзд у подростка {row[COLUMN_NAME]} {row[COLUMN_LASTNAME]}."
                        )
                        return ConversationHandler.END
                    new_stars = current_stars - stars

                sheet_repo.sheet1.update_cell(i + 1, COLUMN_STARS + 1, str(new_stars))
                # comment
                if operation == "add":
                    sheet_repo.add_comment_to_sheet2(
                        int(selected_user_id), "Пополнение", stars, comment
                    )
                    user_gender = sheet_repo.getUserGender(selected_user_id)
                    message = await get_random_notification_message(stars, comment, user_gender)
                    await context.bot.send_message(
                        chat_id=selected_user_id, text=message
                    )
                else:
                    sheet_repo.add_comment_to_sheet2(
                        int(selected_user_id), "Списание", stars, comment
                    )
                dec_stars = await decline_stars_message(stars)
                new_dec_stars = await decline_stars_message(new_stars)
                if stars == 1:
                    await update.message.reply_text(
                        f"{"Добавлена" if operation == "add" else "Списано"} 1 звезда у подростка {row[COLUMN_NAME]} {row[COLUMN_LASTNAME]}. Теперь у него {new_stars} {new_dec_stars}."
                    )
                else:
                    await update.message.reply_text(
                        f"{"Добавлено" if operation == "add" else "Списано"} {stars} {dec_stars} у подростка {row[COLUMN_NAME]} {row[COLUMN_LASTNAME]}. Теперь у него {new_stars} {new_dec_stars}."
                    )
                return ConversationHandler.END

        await update.message.reply_text("Подросток не найден.")
        return ConversationHandler.END

    return handler


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Регистрация остановлена, для продолжения используйте /start.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def handle_teen_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    user_id = callback_data.split("_")[-1]
    context.user_data["selected_user_id"] = user_id
    cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel")
    reply_markup = InlineKeyboardMarkup([[cancel_button]])
    await query.edit_message_text(
        "Введите количество звёзд:", reply_markup=reply_markup
    )
    return ENTER_STARS


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Действие отменено.")
    return ConversationHandler.END


# Просмотр звёзд для админов


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id

    if user_id not in admin_ids:
        return

    sheet_repo = getSheetRepository(context)

    # Получаем все данные из таблицы
    try:
        data = sheet_repo.sheet1.get_all_values()  # Получаем все строки таблицы
    except Exception as e:
        await update.message.reply_text(f"Ошибка при чтении данных из таблицы: {e}")
        return

    # Создаем inline-кнопки с именами и фамилиями
    keyboard = []
    for row in data[1:]:  # Пропускаем первую строку (заголовки)
        user_id_col = row[0]  # Колонка A Id
        name = row[1]  # Колонка B Name
        lastname = row[2]  # Колонка C Lastname
        if name and lastname and user_id_col:
            button = InlineKeyboardButton(
                text=f"{name} {lastname}",
                callback_data=f"user_stars_{user_id_col}",  # Передаем ID пользователя в callback_data
            )
            keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите подростка:", reply_markup=reply_markup)


async def show_user_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Извлекаем ID пользователя из callback_data
    user_id = callback_data.split("_")[-1]

    sheet_repo = getSheetRepository(context)

    try:
        data = sheet_repo.sheet1.get_all_values()  # Получаем все строки таблицы
    except Exception as e:
        await query.edit_message_text(f"Ошибка при чтении данных из таблицы: {e}")
        return

    # Ищем строку с выбранным пользователем
    for row in data:
        if row[0] == user_id:  # Ищем по ID пользователя колонка A
            name = row[1]  # Колонка B Name
            lastname = row[2]  # Колонка C Lastname
            stars = int(
                row[6] if len(row) > 6 and row[6] else "0"
            )  # Колонка L (Stars), если пусто, то 0
            dec_stars_list = await decline_stars_message(stars)
            await query.edit_message_text(
                f"У подростка {name} {lastname} {stars} {dec_stars_list}."
            )
            return

    await query.edit_message_text("Подросток не найден")


# Block and Unblock


async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id

    if user_id not in admin_ids:
        return

    # Получаем данные из таблицы
    sheet_repo = getSheetRepository(context)
    try:
        data = sheet_repo.sheet1.get_all_values()  # Получаем все строки таблицы
    except Exception as e:
        await update.message.reply_text(f"Ошибка при чтении данных из таблицы: {e}")
        return

    # Создаем inline-кнопки с именами и фамилиями
    keyboard = []
    for row in data[1:]:  # Пропускаем первую строку (заголовки)
        user_id_col = row[0]
        name = row[1]
        lastname = row[2]
        if name and lastname and user_id_col:
            button = InlineKeyboardButton(
                text=f"{name} {lastname}",
                callback_data=f"block_user_{user_id_col}",  # Передаем ID пользователя в callback_data
            )
            keyboard.append([button])
    cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel_block")
    keyboard.append([cancel_button])

    await update.message.reply_text(
        "Выберите подростка:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_user_selection_block(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    target_user_id = query.data.replace("block_user_", "")

    context.user_data["target_user_id"] = target_user_id

    sheet_repo = getSheetRepository(context)
    data = sheet_repo.sheet1.get_all_values()
    for row in data[1:]:
        if row[0] == target_user_id:
            name = row[1]
            lastname = row[2]
            break
    keyboard = [
        [
            InlineKeyboardButton(
                "Да ✅", callback_data=f"confirm_block_{target_user_id}"
            )
        ],
        [InlineKeyboardButton("Нет ❌", callback_data="cancel_block")],
    ]

    await query.edit_message_text(
        f"Ограничить доступ подростку {name} {lastname}?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Если нажата кнопка "Да"
    if query.data.startswith("confirm_block_"):
        target_user_id = query.data.replace("confirm_block_", "")

        sheet_repo = getSheetRepository(context)
        data = sheet_repo.sheet1.get_all_values()
        name, lastname = None, None

        for row in data[1:]:  # Пропускаем первую строку (заголовки)
            if row[0] == target_user_id:
                name = row[1]
                lastname = row[2]
                break

        if name and lastname:
            getSheetRepository(context).blockUser(target_user_id)
            await query.edit_message_text(
                f"Подростоку {name} {lastname} ограничен доступ."
            )
        else:
            await query.edit_message_text("Выберите подростка нажатием на кнопку.")

    # Если нажата кнопка "Нет"
    elif query.data == "cancel_block":
        await query.edit_message_text("Действие отменено.")


async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id

    if user_id not in admin_ids:
        return

    # Получаем данные из таблицы
    sheet_repo = getSheetRepository(context)
    try:
        data = sheet_repo.sheet1.get_all_values()  # Получаем все строки таблицы
    except Exception as e:
        await update.message.reply_text(f"Ошибка при чтении данных из таблицы: {e}")
        return

    # Создаем inline-кнопки с именами и фамилиями
    keyboard = []
    for row in data[1:]:  # Пропускаем первую строку (заголовки)
        user_id_col = row[0]
        name = row[1]
        lastname = row[2]
        if name and lastname and user_id_col:
            button = InlineKeyboardButton(
                text=f"{name} {lastname}",
                callback_data=f"unblock_user_{user_id_col}",  # Передаем ID пользователя в callback_data
            )
            keyboard.append([button])
    cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel_block")
    keyboard.append([cancel_button])

    await update.message.reply_text(
        "Выберите подростка:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_user_selection_unblock(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    target_user_id = query.data.replace("unblock_user_", "")

    context.user_data["target_user_id"] = target_user_id

    sheet_repo = getSheetRepository(context)
    data = sheet_repo.sheet1.get_all_values()
    for row in data[1:]:
        if row[0] == target_user_id:
            name = row[1]
            lastname = row[2]
            break
    keyboard = [
        [
            InlineKeyboardButton(
                "Да ✅", callback_data=f"confirm_unblock_{target_user_id}"
            )
        ],
        [InlineKeyboardButton("Нет ❌", callback_data="cancel_unblock")],
    ]

    await query.edit_message_text(
        f"Разрешить доступ подростку {name} {lastname}?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_confirmation1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Если нажата кнопка "Да"
    if query.data.startswith("confirm_unblock_"):
        target_user_id = query.data.replace("confirm_unblock_", "")

        sheet_repo = getSheetRepository(context)
        data = sheet_repo.sheet1.get_all_values()
        name, lastname = None, None

        for row in data[1:]:  # Пропускаем первую строку (заголовки)
            if row[0] == target_user_id:
                name = row[1]
                lastname = row[2]
                break

        if name and lastname:
            getSheetRepository(context).unblockUser(target_user_id)
            await query.edit_message_text(
                f"Подростоку {name} {lastname} разрешен доступ."
            )
        else:
            await query.edit_message_text("Выберите подростка нажатием на кнопку.")

    # Если нажата кнопка "Нет"
    elif query.data == "cancel_unblock":
        await query.edit_message_text("Действие отменено.")


import random

def decline_text_by_number(value: int, text1: str, text2to4: str, textMore: str) -> str:
    """Склоняет слова в зависимости от числа"""
    if 11 <= value % 100 <= 19:
        return textMore
    last_digit = value % 10
    if last_digit == 1:
        return text1
    elif 2 <= last_digit <= 4:
        return text2to4
    else:
        return textMore

async def get_random_notification_message(stars: int, comment: str, user_gender: str):
    # Определяем формы по полу
    if user_gender == "Женский":
        verb_forms = ("получила", "получила", "получила")
        caught_forms = ("поймала", "поймала", "поймала")
        compliment = "Молодец!"
    else:
        verb_forms = ("получил", "получил", "получил")
        caught_forms = ("поймал", "поймал", "поймал")
        compliment = "Красавчик!"

    # Склонение слова "звезда" в винительном падеже
    stars_accusative = decline_text_by_number(stars, "звезду", "звезды", "звёзд")

    # Формы для фразы с "упала звезда" (именительный падеж)
    fall_forms = (
        f"упала {stars} {decline_text_by_number(stars, 'звезда', 'звезды', 'звёзд')}",
        f"упали {stars} {decline_text_by_number(stars, 'звезда', 'звезды', 'звёзд')}",
        f"упало {stars} {decline_text_by_number(stars, 'звезда', 'звезды', 'звёзд')}"
    )

    NOTIFICATION_MESSAGES = [
        f"🚀 Круто! Ты {decline_text_by_number(stars, *verb_forms)} {stars} {stars_accusative} за то, что ты {comment}. {compliment}",
        f"🌟 Бум! На твой счёт {decline_text_by_number(stars, *fall_forms)} за то, что ты {comment}. Продолжай сиять!",
        f"💫 Эй, звёздный герой! За то, что ты {comment}, ты {decline_text_by_number(stars, *verb_forms)} {stars} {stars_accusative}. Так держать!",
        f"🌠 Ты только что {decline_text_by_number(stars, *caught_forms)} {stars} {stars_accusative} за то, что ты {comment}. {compliment}",
        f"✨ Вау! За то, что ты {comment}, ты {decline_text_by_number(stars, *verb_forms)} {stars} {stars_accusative}! {compliment}",
    ]
    rand = random.choice(NOTIFICATION_MESSAGES)
    if user_gender == "Женский" and "звёздный герой!" in rand:
        rand = f"💫 Эй, звёздная героиня! За то, что ты {comment}, ты {decline_text_by_number(stars, *verb_forms)} {stars} {stars_accusative}. Так держать!"
        return rand
    return rand


async def decline_stars_message(stars: int) -> str:
    return decline_text_by_number(stars, "звезду", "звезды", "звёзд")
