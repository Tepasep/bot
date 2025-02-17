import os
import sqlite3

DB_PATH = 'user_operations.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn