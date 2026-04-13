"""
Integration-тесты для хэндлеров ConversationHandler:
  - stars_enter_amount   — валидация введённого числа
  - stars_show_teens_list / stars_handle_teen_selection — выбор подростка
  - stars_cancel_operation — отмена в любой момент

«Integration» здесь означает, что тестируем полный хэндлер целиком
(включая взаимодействие с context.user_data и context.bot),
но без реального Telegram API — всё замокано.
"""
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from telegram.ext import ConversationHandler
from bot_stars.commands import (
    ENTER_STARS,
    ENTER_COMMENT,
    stars_enter_amount,
    stars_handle_teen_selection,
    stars_show_teens_list,
    stars_cancel_operation,
)
from tests.factories import make_context, make_update, make_update_with_query, make_sheet_repo


# ---------------------------------------------------------------------------
# stars_enter_amount
# ---------------------------------------------------------------------------

class TestStarsEnterAmount:
    def _ctx(self):
        return make_context(
            user_data={"operation": "add", "stars_message_id": 10},
        )

    async def test_valid_number_returns_enter_comment(self):
        ctx = self._ctx()
        upd = make_update(text="5")
        result = await stars_enter_amount(upd, ctx)
        assert result == ENTER_COMMENT

    async def test_valid_number_stored_in_context(self):
        ctx = self._ctx()
        upd = make_update(text="7")
        await stars_enter_amount(upd, ctx)
        assert ctx.user_data["stars_amount"] == 7

    async def test_zero_returns_enter_stars(self):
        ctx = self._ctx()
        upd = make_update(text="0")
        result = await stars_enter_amount(upd, ctx)
        assert result == ENTER_STARS

    async def test_negative_returns_enter_stars(self):
        ctx = self._ctx()
        upd = make_update(text="-3")
        result = await stars_enter_amount(upd, ctx)
        assert result == ENTER_STARS

    async def test_non_number_returns_enter_stars(self):
        ctx = self._ctx()
        upd = make_update(text="много")
        result = await stars_enter_amount(upd, ctx)
        assert result == ENTER_STARS

    async def test_float_returns_enter_stars(self):
        ctx = self._ctx()
        upd = make_update(text="3.5")
        result = await stars_enter_amount(upd, ctx)
        assert result == ENTER_STARS

    async def test_empty_string_returns_enter_stars(self):
        ctx = self._ctx()
        upd = make_update(text="")
        result = await stars_enter_amount(upd, ctx)
        assert result == ENTER_STARS

    async def test_prompt_message_sent_on_valid(self):
        ctx = self._ctx()
        upd = make_update(text="5")
        await stars_enter_amount(upd, ctx)
        upd.message.reply_text.assert_called_once()
        call_text = upd.message.reply_text.call_args[0][0]
        assert "комментарий" in call_text.lower()

    async def test_error_message_sent_on_invalid(self):
        ctx = self._ctx()
        upd = make_update(text="abc")
        await stars_enter_amount(upd, ctx)
        upd.message.reply_text.assert_called_once()

    @pytest.mark.parametrize("n", [1, 10, 100, 999])
    async def test_large_valid_numbers_accepted(self, n):
        ctx = self._ctx()
        upd = make_update(text=str(n))
        result = await stars_enter_amount(upd, ctx)
        assert result == ENTER_COMMENT
        assert ctx.user_data["stars_amount"] == n

    async def test_comment_message_id_saved(self):
        ctx = self._ctx()
        upd = make_update(text="3")
        await stars_enter_amount(upd, ctx)
        assert "comment_message_id" in ctx.user_data


# ---------------------------------------------------------------------------
# stars_show_teens_list
# ---------------------------------------------------------------------------

class TestStarsShowTeensList:
    async def test_keyboard_has_all_teens(self):
        repo = make_sheet_repo(rows=[
            ["111", "Иван",  "Иванов",  "", "", "1", "10", "Мужской"],
            ["222", "Мария", "Петрова", "", "", "1", "5",  "Женский"],
            ["333", "Павел", "Сидоров", "", "", "1", "0",  "Мужской"],
        ])
        ctx = make_context(user_data={"operation": "add"}, sheet_repo=repo)
        upd = make_update()

        await stars_show_teens_list(upd, ctx)

        call_kwargs = upd.message.reply_text.call_args[1]
        keyboard = call_kwargs["reply_markup"]
        # Три подростка + кнопка «Отмена»
        assert len(keyboard.inline_keyboard) == 4

    async def test_keyboard_contains_cancel_button(self):
        repo = make_sheet_repo()
        ctx = make_context(user_data={"operation": "add"}, sheet_repo=repo)
        upd = make_update()

        await stars_show_teens_list(upd, ctx)

        call_kwargs = upd.message.reply_text.call_args[1]
        keyboard = call_kwargs["reply_markup"]
        all_callbacks = [
            btn.callback_data
            for row in keyboard.inline_keyboard
            for btn in row
        ]
        assert "stars_cancel_operation" in all_callbacks

    async def test_teen_button_callback_format(self):
        repo = make_sheet_repo()
        ctx = make_context(user_data={"operation": "add"}, sheet_repo=repo)
        upd = make_update()

        await stars_show_teens_list(upd, ctx)

        call_kwargs = upd.message.reply_text.call_args[1]
        keyboard = call_kwargs["reply_markup"]
        teen_callbacks = [
            btn.callback_data
            for row in keyboard.inline_keyboard
            for btn in row
            if btn.callback_data != "stars_cancel_operation"
        ]
        for cb in teen_callbacks:
            assert cb.startswith("stars_select_teen_")

    async def test_sheet_error_ends_conversation(self):
        repo = make_sheet_repo()
        repo.sheet1.get_all_values.side_effect = Exception("API error")
        ctx = make_context(user_data={"operation": "add"}, sheet_repo=repo)
        upd = make_update()

        result = await stars_show_teens_list(upd, ctx)
        assert result == ConversationHandler.END

    async def test_stores_selection_message_id(self):
        repo = make_sheet_repo()
        ctx = make_context(user_data={"operation": "add"}, sheet_repo=repo)
        upd = make_update()

        await stars_show_teens_list(upd, ctx)
        assert "selection_message_id" in ctx.user_data
        assert "selection_chat_id" in ctx.user_data


# ---------------------------------------------------------------------------
# stars_handle_teen_selection
# ---------------------------------------------------------------------------

class TestStarsHandleTeenSelection:
    def _ctx(self, operation="add"):
        repo = make_sheet_repo()
        cell = MagicMock()
        cell.row = 2
        repo.sheet1.find.return_value = cell
        repo.sheet1.cell.side_effect = lambda row, col: MagicMock(
            value="Иван" if col == 2 else "Иванов"
        )
        return make_context(
            user_data={
                "operation": operation,
                "selection_message_id": 7,
                "selection_chat_id": 1,
            },
            sheet_repo=repo,
        )

    async def test_returns_enter_stars_on_selection(self):
        ctx = self._ctx()
        upd = make_update_with_query(data="stars_select_teen_111")
        result = await stars_handle_teen_selection(upd, ctx)
        assert result == ENTER_STARS

    async def test_stores_teen_id(self):
        ctx = self._ctx()
        upd = make_update_with_query(data="stars_select_teen_111")
        await stars_handle_teen_selection(upd, ctx)
        assert ctx.user_data["selected_teen_id"] == "111"

    async def test_stores_teen_name(self):
        ctx = self._ctx()
        upd = make_update_with_query(data="stars_select_teen_111")
        await stars_handle_teen_selection(upd, ctx)
        assert "Иван" in ctx.user_data["selected_teen_name"]

    async def test_sends_stars_prompt(self):
        ctx = self._ctx()
        upd = make_update_with_query(data="stars_select_teen_111")
        await stars_handle_teen_selection(upd, ctx)
        upd.callback_query.message.reply_text.assert_called_once()

    async def test_stars_message_id_stored(self):
        ctx = self._ctx()
        upd = make_update_with_query(data="stars_select_teen_111")
        await stars_handle_teen_selection(upd, ctx)
        assert "stars_message_id" in ctx.user_data

    async def test_cancel_ends_conversation(self):
        ctx = self._ctx()
        upd = make_update_with_query(data="stars_cancel_operation")
        result = await stars_handle_teen_selection(upd, ctx)
        assert result == ConversationHandler.END


# ---------------------------------------------------------------------------
# stars_cancel_operation
# ---------------------------------------------------------------------------

class TestStarsCancelOperation:
    def _ctx_with_data(self):
        return make_context(
            user_data={
                "selected_teen_id": "111",
                "selected_teen_name": "Иван Иванов",
                "stars_amount": 5,
                "operation": "add",
                "selection_message_id": 7,
                "selection_chat_id": 1,
                "stars_message_id": 8,
                "comment_message_id": 9,
            }
        )

    async def test_returns_end(self):
        ctx = self._ctx_with_data()
        upd = make_update_with_query(data="stars_cancel_operation")
        result = await stars_cancel_operation(upd, ctx)
        assert result == ConversationHandler.END

    async def test_context_is_cleaned(self):
        ctx = self._ctx_with_data()
        upd = make_update_with_query(data="stars_cancel_operation")
        await stars_cancel_operation(upd, ctx)
        for key in ("selected_teen_id", "selected_teen_name", "stars_amount",
                    "operation", "selection_message_id", "selection_chat_id",
                    "stars_message_id", "comment_message_id"):
            assert key not in ctx.user_data, f"Ключ '{key}' остался в контексте"

    async def test_cancel_message_shown(self):
        ctx = self._ctx_with_data()
        upd = make_update_with_query(data="stars_cancel_operation")
        await stars_cancel_operation(upd, ctx)
        upd.callback_query.edit_message_text.assert_called_once()
        text = upd.callback_query.edit_message_text.call_args[0][0]
        assert "отменено" in text.lower() or "отмена" in text.lower()

    async def test_cancel_without_context_data_does_not_raise(self):
        """Отмена без предварительно сохранённых данных не должна падать."""
        ctx = make_context(user_data={})
        upd = make_update_with_query(data="stars_cancel_operation")
        result = await stars_cancel_operation(upd, ctx)
        assert result == ConversationHandler.END
