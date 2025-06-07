from telegram import (
    KeyboardButton,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import random
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


NAME, LASTNAME, BIRTHDATE, GENDER, PHONE = range(5)
SELECT_TEEN, ENTER_STARS, ENTER_COMMENT = range(3)
ANSWER_INPUT, REJECT_CONFIRMATION = range(2)

# Клавиатура
async def send_menu_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, admin_ids: list):
    if user_id in admin_ids:
        await update.message.reply_text(
            "Используй команды ниже:",
            parse_mode="Markdown",
            reply_markup=ADMIN_MENU_KEYBOARD
        )
    else:
        await update.message.reply_text(
            "Используй кнопки ниже:",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    return ConversationHandler.END
async def replace_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    cancel_keyboard = ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
    await update.message.reply_text(
        text=text,
        reply_markup=cancel_keyboard
    )
    # метка 
    context.user_data['awaiting_cancel'] = True

async def remove_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    admin_ids_str = os.getenv("ADMIN_ID")
    admin_ids_str = admin_ids_str.replace('"', "").replace("'", "")
    admin_ids = [int(id.strip()) for id in admin_ids_str.split(",")]
    if update.message.text == "❌ Отмена":
        await update.message.reply_text(
            "Действие отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.pop('awaiting_cancel', None)

        await send_menu_keyboard(update, context, user_id, admin_ids)
        return ConversationHandler.END


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
            await send_menu_keyboard(update, context, user_id, admin_ids)
            return

        await send_menu_keyboard(update, context, user_id, admin_ids)
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


async def handle_menu(update, context):
    text = update.message.text
    user_data = context.user_data
    if user_data.get('answering_question'):
        return None
    if text == "❌ Отмена":
        await remove_keyboard(update, context)
        return ConversationHandler.END

    if text == BTN_BALANCE:
        return await viewstars(update, context)
    elif text == BTN_HELP:
        return await start_question_flow(update, context)
    elif text == BTN_ADMIN_LIST:
        return await list_users(update, context)
    elif text == BTN_ADMIN_ADDSTARS:
        return await add_stars(update, context)
    elif text == BTN_ADMIN_REMSTARS:
        return await remstars(update, context)
    elif text == BTN_ADMIN_BLOCK:
        return await block_user(update, context)
    elif text == BTN_ADMIN_UNBLOCK:
        return await unblock_user(update, context)
    elif text == BTN_TOP:
        return await top(update, context)
    elif text == BTN_ADMIN_QUESTIONS:
        return await active_questions(update, context)
    else:
        await update.message.reply_text("Выбери вариант из меню.")

async def add_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id
    if user_id not in admin_ids:
        return
    
    context.user_data['operation'] = 'add'  # Сохраняем тип операции
    await select_teen(update, context)

async def remstars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
    user_id = update.message.from_user.id
    if user_id not in admin_ids:
        return
    
    context.user_data['operation'] = 'rem'  # Сохраняем тип операции
    await select_teen(update, context)


async def start_question_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_question'] = True
    await update.message.reply_text("Напиши свой вопрос:")
    return "HANDLING_QUESTION"

async def handle_user_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    user_id = update.message.from_user.id
    sheet_repo = getSheetRepository(context)
    
    try:
        question_id = sheet_repo.add_question(user_id, question)
        if question_id == -1:
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
            return ConversationHandler.END

        user_info = sheet_repo.get_user_info(user_id)
        admin_message = (
            f"Новый вопрос #{question_id}\n"
            f"От: {user_info['name']} {user_info['lastname']}\n"
            f"Вопрос: {question}"
        )

        keyboard = [
            [InlineKeyboardButton("Ответить", callback_data=f"answer_{question_id}"),
             InlineKeyboardButton("Отклонить", callback_data=f"reject_{question_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        admin_ids = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Ошибка отправки сообщения админу {admin_id}: {e}")

        await update.message.reply_text(f"Мы постараемся ответить на твой вопрос как можно быстрее. ID: #{question_id}")
    except Exception as e:
        print(f"Ошибка обработки вопроса: {e}")
        await update.message.reply_text("Произошла ошибка при обработке вопроса.")
    finally:
        context.user_data.pop('awaiting_question', None)
    
    return ConversationHandler.END

async def active_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet_repo = getSheetRepository(context)
    questions = sheet_repo.get_active_questions()
    
    if not questions:
        await update.message.reply_text("Нет активных вопросов.")
        return
    
    questions_list = []
    keyboard = []
    
    for i, q in enumerate(questions, 1):
        q_text = q.get('question', 'Ошибка в получении текста') 
        # Обрезаем длинный текст вопроса
        short_question = (q_text[:500] + '...') if len(q_text) > 500 else q_text
        questions_list.append(
            f"{i}) #{q['Id']} от {q['name']} {q['lastname']}: {short_question}"
        )
        keyboard.append([InlineKeyboardButton(str(i), callback_data=f"select_{q['Id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Активные вопросы:\n" + "\n".join(questions_list),
        reply_markup=reply_markup
    )

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("select_teen_"):
        return
    
    try:
        if data.startswith("answer_"):
            question_id = data.split("_")[1]
            context.user_data['current_question'] = question_id
            context.user_data['answering_question'] = True
            await query.message.reply_text(f"Введите ответ на вопрос #{question_id}:")
            return ANSWER_INPUT
        
        elif data.startswith("reject_"):
            question_id = data.split("_")[1]
            sheet_repo = getSheetRepository(context)
            if sheet_repo.update_question(int(question_id), "", "Закрыт"):
                try:
                    await query.edit_message_text(f"Вопрос #{question_id} отклонён")
                except:
                    await query.message.reply_text(f"Вопрос #{question_id} отклонён")
            return ConversationHandler.END
        
        elif data.startswith("select_"):
            question_id = data.split("_")[1]
            context.user_data['current_question'] = question_id
            context.user_data['answering_question'] = True
            await query.message.reply_text(f"Введите ответ на вопрос #{question_id}:")
            return ANSWER_INPUT
            
    except Exception as e:
        print(f"ошибка в handle_admin_actions: {e}")
        await query.message.reply_text("Произошла ошибка")
    return ConversationHandler.END

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем наличие необходимых данных
    if 'current_question' not in context.user_data:
        await update.message.reply_text("⚠️ Не удалось найти вопрос для ответа. Попробуйте начать заново.")
        return ConversationHandler.END

    answer = update.message.text
    question_id = context.user_data['current_question']
    
    try:
        sheet_repo = getSheetRepository(context)
        if not sheet_repo.update_question(int(question_id), answer, "Закрыт"):
            await update.message.reply_text("❌ Ошибка при сохранении ответа")
            return ConversationHandler.END

        # Отправка ответа пользователю
        try:
            cell = sheet_repo.sheet3.find(str(question_id))
            if cell:
                user_id = sheet_repo.sheet3.cell(cell.row, 2).value
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📩 Ответ на ваш вопрос #{question_id}:\n{answer}"
                )
        except Exception as e:
            print(f"Ошибка отправки ответа пользователю: {e}")

        await update.message.reply_text("✅ Ответ отправлен")
        
    except Exception as e:
        print(f"Ошибка в handle_answer: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обработке")
        
    finally:
        # Всегда очищаем данные
        context.user_data.pop('current_question', None)
        context.user_data.pop('answering_question', None)
    
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
                "Кажется, ты ввел неверную дату. Повтори ввод (формат ДД.ММ.ГГГГ)."
            )
            context.user_data["last_bot_message_id"] = sent_message.message_id
            return BIRTHDATE

        context.user_data["birthdate"] = birthdate_str

        # Создаем клавиатуру для выбора пола
        reply_keyboard = [["Мужской", "Женский"]]
        sent_message = await update.message.reply_text(
            "Выбери свой пол:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, resize_keyboard=True, one_time_keyboard=True
            ),
        )
        context.user_data["last_bot_message_id"] = sent_message.message_id
        return GENDER

    except ValueError:
        sent_message = await update.message.reply_text(
            "Неверный формат даты. Введи дату в формате ДД.ММ.ГГГГ."
        )
        context.user_data["last_bot_message_id"] = sent_message.message_id
        return BIRTHDATE


async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    gender_str = update.message.text
    if gender_str == "Отменить":
        return await cancel(update, context)

    if gender_str not in ["Мужской", "Женский"]:  # Исправлено здесь
        sent_message = await update.message.reply_text(
            "Выберите пол, используя кнопки ниже."
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
                f"Ты успешно зарегистрирован, используй /start",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await update.message.reply_text(
                f"Ты успешно зарегистрирован, используй /start",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove(),
            )
    elif gender == "Женский":
        if user_id in admin_ids:
            await update.message.reply_text(
                f"Ты успешно зарегистрирована, используй /start",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await update.message.reply_text(
                f"Ты успешно зарегистрирована, используй /start",
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
                text=f"{name} {lastname}",
                callback_data=f"select_teen_{user_id_col}"
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
        # Получаем тип операции из context.user_data
        operation = context.user_data.get('operation', 'add')
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
                        f"{'Добавлена' if operation == 'add' else 'Списано'} 1 звезда у подростка {row[COLUMN_NAME]} {row[COLUMN_LASTNAME]}. Теперь у него {new_stars} {new_dec_stars}."
                    )
                else:
                    await update.message.reply_text(
                        f"{'Добавлено' if operation == 'add' else 'Списано'} {stars} {dec_stars} у подростка {row[COLUMN_NAME]} {row[COLUMN_LASTNAME]}. Теперь у него {new_stars} {new_dec_stars}."
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
    await query.answer()  # Это важно для подтверждения нажатия
    
    try:
        # Получаем ID подростка из callback_data
        teen_id = query.data.split('_')[-1]
        context.user_data["selected_user_id"] = teen_id
        
        # Создаем кнопку отмены
        keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Редактируем сообщение вместо отправки нового
        await query.edit_message_text(
            text="Введите количество звёзд:",
            reply_markup=reply_markup
        )
        return ENTER_STARS
    except Exception as e:
        print(f"Ошибка в handle_teen_selection: {e}")
        await query.message.reply_text("Произошла ошибка при выборе подростка")
        return ConversationHandler.END



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


async def handle_user_selection_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
