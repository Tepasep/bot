import sqlite3
from datetime import datetime
from ..domain.models import User, Operation
from .database import get_db_connection

class UserRepository:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        """Создание таблиц"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            chatID TEXT NOT NULL UNIQUE,
            telephone TEXT NOT NULL,
            balance REAL DEFAULT 0,
            dr TEXT NOT NULL,
            dcreate TEXT NOT NULL,
            dupdate TEXT,
            ddelete TEXT
        )
        ''')

        self.cursor.execute('''
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
        self.conn.commit()

    def add_user(self, user: User):
        self.cursor.execute('''
        INSERT INTO users (name, surname, chatID, telephone, dr, dcreate)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user.name, user.surname, user.chatID, user.telephone, user.dr, user.dcreate))
        self.conn.commit()

    def get_user_by_chat_id(self, chatID: str):
        self.cursor.execute('SELECT * FROM users WHERE chatID = ?', (chatID,))
        data = self.cursor.fetchone()
        return User(*data) if data else None

class OperationRepository:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def add_operation(self, operation: Operation):
        self.cursor.execute('''
        INSERT INTO operations (user_id, datetime, stars, type, comment)
        VALUES (?, ?, ?, ?, ?)
        ''', (operation.user_id, operation.datetime, operation.stars, operation.type, operation.comment))
        self.conn.commit()