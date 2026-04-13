"""
Фабрики моков — единственное место, где описаны «болванки» объектов telegram.
Импортируются в conftest.py и напрямую в тесты при нетипичных сценариях.
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def make_bot() -> MagicMock:
    bot = MagicMock()
    bot.delete_message = AsyncMock()
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=99))
    return bot


def make_context(user_data: dict | None = None, sheet_repo=None) -> MagicMock:
    ctx = MagicMock()
    ctx.user_data = user_data or {}
    ctx.bot = make_bot()
    ctx.bot_data = {"sheet_repository": sheet_repo} if sheet_repo else {}
    return ctx


def make_message(
    text: str = "тест",
    chat_id: int = 1,
    message_id: int = 10,
    user_id: int = 100,
) -> MagicMock:
    msg = MagicMock()
    msg.text = text
    msg.chat_id = chat_id
    msg.message_id = message_id
    msg.from_user = MagicMock(id=user_id)
    msg.reply_text = AsyncMock(return_value=MagicMock(message_id=20))
    return msg


def make_update(text: str = "тест", chat_id: int = 1, user_id: int = 100) -> MagicMock:
    upd = MagicMock()
    upd.message = make_message(text=text, chat_id=chat_id, user_id=user_id)
    upd.callback_query = None
    return upd


def make_callback_query(
    data: str = "some_data",
    chat_id: int = 1,
    message_id: int = 20,
) -> MagicMock:
    query = MagicMock()
    query.answer = AsyncMock()
    query.delete_message = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = data
    query.message = make_message(chat_id=chat_id, message_id=message_id)
    query.message.chat_id = chat_id
    return query


def make_update_with_query(
    data: str = "some_data",
    chat_id: int = 1,
) -> MagicMock:
    upd = MagicMock()
    upd.callback_query = make_callback_query(data=data, chat_id=chat_id)
    upd.message = None
    return upd


def make_sheet_repo(
    current_stars: int = 10,
    gender: str = "Мужской",
    rows: list[list] | None = None,
) -> MagicMock:
    """
    rows — список строк таблицы (без заголовка).
    Формат: [user_id, name, lastname, birthdate, phone, access, stars, gender]
    """
    repo = MagicMock()

    cell = MagicMock()
    cell.row = 2
    repo.sheet1.find.return_value = cell
    repo.sheet1.cell.return_value.value = str(current_stars)
    repo.sheet1.update_cell = MagicMock()
    repo.add_comment_to_sheet2 = MagicMock()
    repo.getUserGender.return_value = gender

    default_rows = [
        ["111", "Иван", "Иванов", "2008-01-01", "+79001234567", "1", str(current_stars), gender],
        ["222", "Мария", "Петрова", "2009-05-10", "+79007654321", "1", "5", "Женский"],
    ]
    all_values = [
        ["Id", "Name", "Lastname", "Birthdate", "Phone", "Access", "Stars", "Gender"],
        *(rows if rows is not None else default_rows),
    ]
    repo.sheet1.get_all_values.return_value = all_values

    return repo
