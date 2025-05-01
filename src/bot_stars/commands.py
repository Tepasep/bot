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
from bot_stars.keyboards import (
    ADMIN_MENU_KEYBOARD,
    BTN_ADMIN_ADDSTARS,
    BTN_ADMIN_BLOCK,
    BTN_ADMIN_LIST,
    BTN_ADMIN_REMSTARS,
    BTN_ADMIN_UNBLOCK,
    BTN_BALANCE,
    BTN_HELP,
    BTN_TOP,
    MAIN_MENU_KEYBOARD,
    BTN_ADMIN_QUESTIONS,
)

from bot_stars.utils import (
    decline_stars_message,
    decline_text_by_number,
    format_date,
    getSheetRepository,
)
import random


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
                f"Ты администратор, команды для тебя:",
                parse_mode="Markdown",
                reply_markup=ADMIN_MENU_KEYBOARD,
            )
            return

        await update.message.reply_text(
            "Используй кнопки ниже:", reply_markup=MAIN_MENU_KEYBOARD
        )
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


def handle_menu(update, context):
    text = update.message.text
    user_data = context.user_data

    if user_data.get('awaiting_question'):
        return save_question(update, context)

    if text == BTN_BALANCE:
        return viewstars(update, context)
    elif text == BTN_HELP:
        return help_command(update, context)
    elif text == BTN_ADMIN_LIST:
        return list_users(update, context)
    # elif text == BTN_ADMIN_ADDSTARS:
    #     return add_stars(update, context)
    # elif text == BTN_ADMIN_REMSTARS:
    #     return remstars(update, context)
    elif text == BTN_ADMIN_BLOCK:
        return block_user(update, context)
    elif text == BTN_ADMIN_UNBLOCK:
        return unblock_user(update, context)
    elif text == BTN_TOP:
        return top(update, context)
    elif text == BTN_ADMIN_QUESTIONS:
        return show_active_questions(update, context)
    else:
        return for_handle_menu(update, context)
    
async def for_handle_menu(update, context):
    await update.message.reply_text("Пожалуйста, выбери вариант из меню.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data['awaiting_question'] = True
    await update.message.reply_text(
        "Напишите ваш вопрос, и мы постараемся ответить на него как можно быстрее."
    )
    return "AWAITING_QUESTION"

async def save_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    question = update.message.text

    repo = context.bot_data.get('sheet_repository')
    if not repo:
        print("репозиторий не доступен")
        return ConversationHandler.END
    
    # Получаем последний ID вопроса
    try:
        questions = repo.sheet3.get_all_records()
        last_id = max([q['Id'] for q in questions]) if questions else 0
        new_id = last_id + 1
    except Exception as e:
        new_id = 1
    
    # Сохраняем вопрос
    new_question = {
        'Id': new_id,
        'user_id': user.id,
        'question': question,
        'status': 'Активный'
    }
    repo.sheet3.append_row(list(new_question.values()))
    
    await update.message.reply_text("Спасибо за ваш вопрос! Мы ответим вам как можно скорее.")
    
    # Уведомляем админов
    await notify_admins(context.bot, new_id, question, user)
    
    return ConversationHandler.END

async def notify_admins(bot, question_id, question_text, user):
    admin_ids = os.getenv("ADMIN_ID", "").split(",")
    if not admin_ids or not admin_ids[0]:
        print("ОШИБКА: ADMIN_ID не задан в .env файле")
        return

    success = False
    for admin_id in admin_ids:
        try:
            admin_id = admin_id.strip()
            if not admin_id.isdigit():
                print(f"Некорректный ADMIN_ID: {admin_id}")
                continue
                
            await bot.send_message(
                chat_id=int(admin_id),
                text=f"❓ Новый вопрос #{question_id}\n"
                     f"👤 От: {user.first_name} {user.last_name or ''}\n"
                     f"📝 Вопрос: {question_text}\n\n"
            )
            success = True
        except Exception as e:
            print(f"ошибка при отправке уведомления админу {admin_id}: {e}")

    return success


async def show_active_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        repo = context.bot_data['sheet_repository']
        questions = repo.sheet3.get_all_records()
        active_questions = [q for q in questions if str(q.get('status', '')).lower() == 'активный']
        
        if not active_questions:
            await update.message.reply_text("Нет активных вопросов")
            return ConversationHandler.END

        users = repo.sheet1.get_all_records()
        user_dict = {}
        for user in users:
            user_id = str(user.get('id') or user.get('Id') or user.get('user_id'))
            if user_id:
                name = str(user.get('name', '')).strip()
                lastname = str(user.get('lastname', '')).strip()
                user_dict[user_id] = f"{name} {lastname}" if name and lastname else name or lastname or "Аноним"

        buttons = []
        for question in active_questions:
            user_id = str(question.get('user_id', ''))
            username = user_dict.get(user_id, f"ID:{user_id}")
            btn_text = f"#{question.get('Id')} от {username[:15]}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=f"q_{question.get('Id')}")])

        buttons.append([InlineKeyboardButton("❌ Отменить", callback_data="q_cancel")])

        await update.message.reply_text(
            "📋 Активные вопросы:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        context.user_data['active_questions'] = {q['Id']: q for q in active_questions}
        context.user_data['user_dict'] = user_dict  # Сохраняем user_dict в контекст
        return "HANDLE_QUESTION"

    except Exception as e:
        print(f"ERROR in show_active_questions: {e}")
        await update.message.reply_text("Ошибка загрузки вопросов")
        return ConversationHandler.END
    
async def handle_question_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    question_id = int(query.data.split('_')[-1])
    questions = context.user_data.get('active_questions', [])
    
    selected = next((q for q in questions if q.get('Id') == question_id), None)
    if not selected:
        await query.edit_message_text("Вопрос не найден")
        return ConversationHandler.END
    
    context.user_data['selected_question'] = selected
    await query.edit_message_text(
        f"Выбран вопрос #{selected.get('Id')}:\n"
        f"{selected.get('question')}\n\n"
        "Введите ваш ответ:"
    )
    return "AWAITING_ANSWER"

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'q_cancel':
        await query.edit_message_text("Выбор отменен")
        return ConversationHandler.END

    try:
        question_id = int(query.data.split('_')[1])
        questions = context.user_data.get('active_questions', {})
        user_dict = context.user_data.get('user_dict', {})  
        question = questions.get(question_id)
        
        if not question:
            await query.edit_message_text("Вопрос не найден")
            return ConversationHandler.END

        context.user_data['selected_question'] = question
        await query.edit_message_text(
            f"✉️ Вопрос #{question_id}\n"
            f"👤 От: {user_dict.get(str(question.get('user_id')), 'Неизвестно')}\n\n"
            f"📝 {question.get('question')}\n\n"
            "Введите ваш ответ:"
        )
        return "HANDLE_ANSWER"

    except Exception as e:
        print(f"ERROR in handle_question: {e}")
        await query.edit_message_text("Ошибка обработки")
        return ConversationHandler.END

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        answer = update.message.text
        question = context.user_data['selected_question']
        repo = context.bot_data['sheet_repository']
        
        await context.bot.send_message(
            chat_id=question['user_id'],
            text=f"Ответ на ваш вопрос #{question['Id']}:\n\n{answer}"
        )
        
        for i, q in enumerate(repo.sheet3.get_all_records(), 2):
            if q['Id'] == question['Id']:
                repo.sheet3.update_cell(i, 4, 'Закрыт')
                break

        await update.message.reply_text("✅ Ответ отправлен")
        return ConversationHandler.END

    except Exception as e:
        print(f"ERROR in handle_answer: {e}")
        await update.message.reply_text("Ошибка отправки ответа")
        return ConversationHandler.END
    
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
async def cancel_question_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_text("Выбор вопроса отменен")
        return ConversationHandler.END
    except Exception as e:
        print(f"Ошибка в cancel_question_select: {e}")
        return ConversationHandler.END

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

    operations = sheet_repo.get_last_comments(int(user_id), limit=5)
    operations = operations[::-1]

    stars_text = decline_stars_message(int(stars))

    lines = []
    lines.append(f"✨ <b>Твой баланс:</b> {stars} {stars_text}\n")
    lines.append("📜 <b>Последние операции:</b>\n")
    for operation in operations:
        operation_type = operation[1]  # Колонка "Тип операции"
        amount = int(operation[2])  # Колонка "Звёзды"
        comment = operation[3]  # Колонка "Комментарий"
        datetime_str = operation[4]  # Колонка "Дата и время"
        if operation_type == "Пополнение": symbol = "➕"
        else: symbol = "➖"
        lines.append(f"{symbol} <b>{amount}</b> — {comment}")
        lines.append(f"🗓 {format_date(datetime_str)}\n")

    lines.append("ℹ️ Эти звезды ты сможешь обменять на реальные призы в день ярмарки!")
    message = "\n".join(lines)
    await update.message.reply_text(message, parse_mode="HTML")


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
                reply_keyboard, resize_keyboard=True, one_time_keyboard=True
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
        "Отлично! Теперь отправь свой номер телефона:", reply_markup=reply_markup
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
        update.message.contact.phone_number
        if update.message.contact
        else update.message.text
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
            await update.message.reply_text(
                f"Ты успешно зарегистрирован, команды для тебя: \n**1.** /list \n**2.** /addstars \n**3.** /remstars \n**4.** /block \n**5.** /unblock \n**6.** /viewstars",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await update.message.reply_text(
                f"Ты успешно зарегистрирован, для просмотра звёзд используй /viewstars",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove(),
            )
    elif gender == "Женский":
        if user_id in admin_ids:
            await update.message.reply_text(
                f"Ты успешно зарегистрирована, команды для тебя: \n**1.** /list \n**2.** /addstars \n**3.** /remstars \n**4.** /block \n**5.** /unblock \n**6.** /viewstars",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await update.message.reply_text(
                f"Ты успешно зарегистрирована, для просмотра звёзд используй /viewstars",
                parse_mode="Markdown",
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
                    message = await get_random_notification_message(
                        stars, comment, user_gender
                    )
                    await context.bot.send_message(
                        chat_id=selected_user_id, text=message
                    )
                else:
                    sheet_repo.add_comment_to_sheet2(
                        int(selected_user_id), "Списание", stars, comment
                    )
                dec_stars = decline_stars_message(stars)
                new_dec_stars = decline_stars_message(new_stars)
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
            dec_stars_list = decline_stars_message(stars)
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
        f"упало {stars} {decline_text_by_number(stars, 'звезда', 'звезды', 'звёзд')}",
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

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        current_user_id = update.message.from_user.id
        sheet_repo = getSheetRepository(context)
        data = sheet_repo.sheet1.get_all_values()

        current_user_in_top = False
        current_user_data = None
        stars_list =[]
        for row in data[1:]:
            try:
                user_id = int(row[0])
                user = str(row[1]) + ' ' + str(row[2])  # user
                stars = int(row[6])        # stars
                entry = (user_id, user, stars)
                stars_list.append(entry)

                if user_id == current_user_id:
                    current_user_data = entry
            except (IndexError, ValueError) as e:
                print(f"Ошибка в строке {row}: {e}")
                continue

        if not stars_list:
            await update.message.reply_text("ℹ️ Нет данных о звёздах")
            return

        sorted_users = sorted(stars_list, key=lambda x: x[2], reverse=True)
        
        message = ["🏆 Топ по звёздам:"]
        
        # Топ
        top_users = sorted_users[:5]
        for i, (user_id, user_name, stars) in enumerate(top_users, 1):
            # Проверяем, есть ли текущий пользователь в топе
            if user_id == current_user_id:
                current_user_in_top = True
            message.append(f"{i}. {user_name} — {stars} ⭐")
        
        # Показываем место пользователя
        if current_user_data and not current_user_in_top:
            user_place = sorted_users.index(current_user_data) + 1
            message.append(f"... \n{user_place}. {current_user_data[1]} — {current_user_data[2]} ⭐")
        
        await update.message.reply_text("\n".join(message))

    except Exception as e:
        await update.message.reply_text("⚠️ Произошла ошибка.")