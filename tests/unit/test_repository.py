"""
Unit-тесты для SheetsRepository (без реального Google Sheets).

SheetsRepository.__init__ обращается к Google API, поэтому тестируем
методы в изоляции: создаём экземпляр через object.__new__ и подставляем
моки для sheet1/sheet2.

freezegun фиксирует datetime.now() — так проверяем формат временной метки.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, call
from freezegun import freeze_time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from bot_stars.repository import SheetsRepository


def make_repo() -> SheetsRepository:
    """Создать SheetsRepository без вызова __init__ (без Google API)."""
    repo = object.__new__(SheetsRepository)
    repo.sheet1 = MagicMock()
    repo.sheet2 = MagicMock()
    repo.sheet3 = MagicMock()
    return repo


# ---------------------------------------------------------------------------
# add_comment_to_sheet2
# ---------------------------------------------------------------------------

class TestAddCommentToSheet2:
    @freeze_time("2025-06-15 12:30:45")
    def test_appends_correct_row_int_id(self):
        repo = make_repo()
        repo.add_comment_to_sheet2("111", "Пополнение", 5, "помог убраться")
        repo.sheet2.append_row.assert_called_once_with(
            [111, "Пополнение", 5, "помог убраться", "2025-06-15 12:30:45"]
        )

    @freeze_time("2025-06-15 12:30:45")
    def test_appends_correct_row_str_id(self):
        """Если teen_id не конвертируется в int — остаётся строкой."""
        repo = make_repo()
        repo.add_comment_to_sheet2("не_число", "Списание", 3, "прогулял")
        repo.sheet2.append_row.assert_called_once_with(
            ["не_число", "Списание", 3, "прогулял", "2025-06-15 12:30:45"]
        )

    @freeze_time("2025-01-01 00:00:00")
    def test_timestamp_format(self):
        repo = make_repo()
        repo.add_comment_to_sheet2("1", "Пополнение", 1, "тест")
        row = repo.sheet2.append_row.call_args[0][0]
        timestamp = row[4]
        # Формат YYYY-MM-DD HH:MM:SS
        import re
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", timestamp)

    @freeze_time("2025-03-10 09:05:03")
    def test_operation_type_stored(self):
        repo = make_repo()
        repo.add_comment_to_sheet2("42", "Списание", 10, "плохо себя вёл")
        row = repo.sheet2.append_row.call_args[0][0]
        assert row[1] == "Списание"

    @freeze_time("2025-03-10 09:05:03")
    def test_stars_count_stored(self):
        repo = make_repo()
        repo.add_comment_to_sheet2("42", "Пополнение", 7, "хорошо работал")
        row = repo.sheet2.append_row.call_args[0][0]
        assert row[2] == 7

    @freeze_time("2025-03-10 09:05:03")
    def test_comment_stored(self):
        repo = make_repo()
        repo.add_comment_to_sheet2("42", "Пополнение", 7, "моя заметка")
        row = repo.sheet2.append_row.call_args[0][0]
        assert row[3] == "моя заметка"

    @freeze_time("2025-03-10 09:05:03")
    def test_multiple_calls_each_appended(self):
        repo = make_repo()
        repo.add_comment_to_sheet2("1", "Пополнение", 1, "раз")
        repo.add_comment_to_sheet2("2", "Пополнение", 2, "два")
        assert repo.sheet2.append_row.call_count == 2


# ---------------------------------------------------------------------------
# get_next_loc_id
# ---------------------------------------------------------------------------

class TestGetNextLocId:
    def test_empty_sheet_returns_1(self):
        repo = make_repo()
        repo.sheet1.col_values.return_value = ["Id"]  # только заголовок
        assert repo.get_next_loc_id() == 1

    def test_single_entry_returns_2(self):
        repo = make_repo()
        repo.sheet1.col_values.return_value = ["Id", "1"]
        assert repo.get_next_loc_id() == 2

    def test_max_plus_one(self):
        repo = make_repo()
        repo.sheet1.col_values.return_value = ["Id", "3", "7", "2"]
        assert repo.get_next_loc_id() == 8

    def test_non_digit_values_ignored(self):
        repo = make_repo()
        repo.sheet1.col_values.return_value = ["Id", "abc", "5", ""]
        assert repo.get_next_loc_id() == 6

    def test_only_header_no_digits(self):
        repo = make_repo()
        repo.sheet1.col_values.return_value = ["Id", "", ""]
        assert repo.get_next_loc_id() == 1
