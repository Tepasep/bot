from datetime import datetime
from telegram.ext import ContextTypes
from bot_stars.repository import Repository, SheetsRepository


def getRepository(context: ContextTypes.DEFAULT_TYPE):
    repository: Repository = context.bot_data.get("repository")
    return repository


def getSheetRepository(context: ContextTypes.DEFAULT_TYPE):
    repository: SheetsRepository = context.bot_data.get("sheet_repository")
    return repository


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


def decline_stars_message(stars: int) -> str:
    return decline_text_by_number(stars, "звезду", "звезды", "звёзд")


def format_date(date_str):
    """
    Функция для преобразования строки даты в формат "20 марта 2025".

    :param date_str: Дата в формате "YYYY-MM-DD HH:MM:SS".
    :return: Дата в формате "ДД месяц ГГГГ".
    """
    # Преобразуем строку в объект datetime
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    # Форматируем дату в нужный формат
    formatted_date = date_obj.strftime("%d %B %Y")

    # Переводим месяц на русский
    months = {
        "January": "января",
        "February": "февраля",
        "March": "марта",
        "April": "апреля",
        "May": "мая",
        "June": "июня",
        "July": "июля",
        "August": "августа",
        "September": "сентября",
        "October": "октября",
        "November": "ноября",
        "December": "декабря",
    }

    # Заменяем англоязычные месяцы на русские
    formatted_date = formatted_date.replace(
        date_obj.strftime("%B"), months[date_obj.strftime("%B")]
    )

    return formatted_date
