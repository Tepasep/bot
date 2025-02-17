import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

# db
conn = sqlite3.connect('user_operations.db', check_same_thread=False)
cursor = conn.cursor()

# id admin lists
ADMIN_ID = [2048674393, ]

# db
def init_db():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        surname TEXT NOT NULL,
        chatID TEXT NOT NULL,
        telephone TEXT NOT NULL,
        balance REAL DEFAULT 0,
        dr TEXT NOT NULL,
        dcreate TEXT NOT NULL,
        dupdate TEXT,
        ddelete TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        datetime TEXT NOT NULL,
        stars INTEGER NOT NULL,
        type TEXT NOT NULL,
        comment TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()

# check admin
def is_admin(user_id):
    return user_id in ADMIN_ID

# /adduser (admin)
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        args = context.args
        if len(args) != 5:
            await update.message.reply_text("Использование: /adduser <Имя> <Фамилия> <ID> <Телефон> <Дата рождения>")
            return

        name, surname, chatID, telephone, dr = args
        dcreate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
        INSERT INTO users (name, surname, chatID, telephone, dr, dcreate)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, surname, chatID, telephone, dr, dcreate))
        conn.commit()

        await update.message.reply_text(f"Пользователь {name} {surname} успешно добавлен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# /addstars (admin)
async def add_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Использование: /addstars <ID> <количество звёзд> <комментарий>")
            return

        user_id_op, stars = int(args[0]), int(args[1])
        comment = ' '.join(args[2:]) if len(args) > 2 else None

        datetime_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO operations (user_id, datetime, stars, type, comment)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id_op, datetime_now, stars, 'пополнение', comment))

        cursor.execute('''
        UPDATE users SET balance = balance + ? WHERE id = ?
        ''', (stars, user_id_op))
        conn.commit()

        await update.message.reply_text(f"Начислено {stars} звезд пользователю с ID {user_id_op}.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# /removestars (admin)
async def remove_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Использование: /removestars <user_id> <stars> <comment>")
            return

        user_id_op, stars = int(args[0]), int(args[1])
        comment = ' '.join(args[2:]) if len(args) > 2 else None

        datetime_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO operations (user_id, datetime, stars, type, comment)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id_op, datetime_now, stars, 'списание', comment))

        cursor.execute('''
        UPDATE users SET balance = balance - ? WHERE id = ?
        ''', (stars, user_id_op))
        conn.commit()

        await update.message.reply_text(f"Списано {stars} звезд у пользователя с ID {user_id_op}.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# /deleteuser (admin)
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("Использование: /deleteuser <user_id>")
            return

        user_id_op = int(args[0])
        ddelete = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
        UPDATE users SET ddelete = ? WHERE id = ?
        ''', (ddelete, user_id_op))
        conn.commit()

        await update.message.reply_text(f"Пользователь с ID {user_id_op} отключен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# /viewstars (public)
async def view_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    try:
        cursor.execute('SELECT ddelete FROM users WHERE chatID = ?', (str(user_id),))
        ddelete = cursor.fetchone()

        if ddelete and ddelete[0]:
            await update.message.reply_text("Ваш аккаунт отключен.")
            return

        cursor.execute('SELECT balance FROM users WHERE chatID = ?', (str(user_id),))
        balance = cursor.fetchone()

        if not balance:
            await update.message.reply_text("Ваш профиль не подключен.")
            return

        cursor.execute('''
        SELECT datetime, stars, type, comment FROM operations
        WHERE user_id = (SELECT id FROM users WHERE chatID = ?)
        ORDER BY datetime DESC
        ''', (str(user_id),))
        operations = cursor.fetchall()

        message = f"Ваш баланс: {balance[0]} звезд.\n\nИстория операций:\n"
        for op in operations:
            message += f"{op[0]} | {op[2]} {op[1]} звезд | {op[3]}\n"

        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# /listusers (admin)
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    try:
        cursor.execute('''
        SELECT id, name, surname, chatID, telephone, balance, dr, dcreate, dupdate, ddelete
        FROM users
        ''')
        users = cursor.fetchall()

        if not users:
            await update.message.reply_text("Пользователи не найдены.")
            return

        message = "Список пользователей:\n"
        for user in users:
            user_id, name, surname, chatID, telephone, balance, dr, dcreate, dupdate, ddelete = user

            status = "Активен" if ddelete is None else f"Отключен ({ddelete})"

            message += (
                f"ID: {user_id}, {name} {surname}, Дата рождения: {dr} "
                f"ChatID: {chatID}, {telephone}, Баланс: {balance}, "
                f"Дата создания: {dcreate}, Статус: {status}\n\n "
            )

        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет, я твой бот для отслеживания звёзд. Для просмотра звёзд используй команду /viewstars."
    )
    
# /admin (admin)
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id): 
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return


    await update.message.reply_text(
        "Вот список доступных команд для администраторов:\n"
        "/adduser - Добавить пользователя\n"
        "/addstars - Начислить звёзды\n"
        "/removestars - Списать звёзды\n"
        "/deleteuser - Отключить пользователя\n"
        "/listusers - Список всех пользователей\n"
        "/admin - Это сообщение"
    )

# main
def main():
    init_db()

    # token
    TOKEN = 'token'

    application = Application.builder().token(TOKEN).build()

    # Command
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin))
    application.add_handler(CommandHandler('adduser', add_user))
    application.add_handler(CommandHandler('addstars', add_stars))
    application.add_handler(CommandHandler('removestars', remove_stars))
    application.add_handler(CommandHandler('deleteuser', delete_user))
    application.add_handler(CommandHandler('viewstars', view_stars))
    application.add_handler(CommandHandler('listusers', list_users))

    # start
    application.run_polling()

if __name__ == '__main__':
    main()