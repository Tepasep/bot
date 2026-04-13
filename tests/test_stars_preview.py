"""
Тесты для функционала предпросмотра сообщения при начислении звёзд.

Фикстуры приходят из tests/conftest.py, фабрики — из tests/factories.py.

Покрываемые сценарии:
  - stars_enter_comment: добавление → показ предпросмотра
  - stars_enter_comment: списание   → немедленная обработка
  - stars_preview_action: confirm   → операция выполнена, уведомление отправлено
  - stars_preview_action: edit      → запрос нового комментария, возврат в ENTER_COMMENT
  - _stars_process_operation        → начисление / списание / недостаточно звёзд
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from telegram.ext import ConversationHandler
from bot_stars.commands import (
    ENTER_COMMENT,
    PREVIEW_MESSAGE,
    _stars_process_operation,
    stars_enter_comment,
    stars_preview_action,
)
from tests.factories import make_context, make_update, make_update_with_query, make_sheet_repo


# ---------------------------------------------------------------------------
# stars_enter_comment — добавление звёзд (используем фикстуры conftest)
# ---------------------------------------------------------------------------

class TestStarsEnterCommentAdd:
    async def test_returns_preview_message_state(self, add_ctx, comment_update):
        result = await stars_enter_comment(comment_update, add_ctx)
        assert result == PREVIEW_MESSAGE

    async def test_saves_pending_comment(self, add_ctx, comment_update):
        await stars_enter_comment(comment_update, add_ctx)
        assert add_ctx.user_data["pending_comment"] == comment_update.message.text

    async def test_saves_pending_notification(self, add_ctx, comment_update):
        await stars_enter_comment(comment_update, add_ctx)
        assert "pending_notification" in add_ctx.user_data
        assert comment_update.message.text in add_ctx.user_data["pending_notification"]

    async def test_preview_contains_teen_name(self, add_ctx, comment_update):
        await stars_enter_comment(comment_update, add_ctx)
        call_text = comment_update.message.reply_text.call_args[0][0]
        assert "Иван" in call_text

    async def test_preview_text_shows_предпросмотр(self, add_ctx, comment_update):
        await stars_enter_comment(comment_update, add_ctx)
        call_text = comment_update.message.reply_text.call_args[0][0]
        assert "Предпросмотр" in call_text

    async def test_keyboard_has_confirm_and_edit_buttons(self, add_ctx, comment_update):
        await stars_enter_comment(comment_update, add_ctx)
        _, kwargs = comment_update.message.reply_text.call_args
        buttons = kwargs["reply_markup"].inline_keyboard[0]
        callbacks = {btn.callback_data for btn in buttons}
        assert "stars_confirm_send" in callbacks
        assert "stars_edit_comment" in callbacks

    async def test_preview_message_id_stored(self, add_ctx, comment_update):
        await stars_enter_comment(comment_update, add_ctx)
        assert "preview_message_id" in add_ctx.user_data

    async def test_female_teen_also_gets_preview(self, add_ctx_female):
        upd = make_update(text="пела в хоре")
        result = await stars_enter_comment(upd, add_ctx_female)
        assert result == PREVIEW_MESSAGE
        assert "пела в хоре" in add_ctx_female.user_data["pending_notification"]


# ---------------------------------------------------------------------------
# stars_enter_comment — списание (немедленная обработка)
# ---------------------------------------------------------------------------

class TestStarsEnterCommentRemove:
    async def test_returns_end_state(self, rem_ctx):
        upd = make_update(text="плохо себя вёл")
        result = await stars_enter_comment(upd, rem_ctx)
        assert result == ConversationHandler.END

    async def test_no_preview_message_sent(self, rem_ctx):
        upd = make_update(text="плохо себя вёл")
        await stars_enter_comment(upd, rem_ctx)
        upd.message.reply_text.assert_not_called()

    async def test_stars_updated(self, rem_ctx):
        repo = rem_ctx.bot_data["sheet_repository"]
        upd = make_update(text="прогулял")
        await stars_enter_comment(upd, rem_ctx)
        # 10 - 3 = 7
        repo.sheet1.update_cell.assert_called_once_with(2, 7, "7")

    async def test_success_sent_to_admin(self, rem_ctx):
        upd = make_update(text="прогулял")
        await stars_enter_comment(upd, rem_ctx)
        rem_ctx.bot.send_message.assert_called()
        text = rem_ctx.bot.send_message.call_args[1]["text"]
        assert "Успешно" in text

    async def test_insufficient_stars_ends(self, rem_ctx_insufficient):
        upd = make_update(text="причина")
        result = await stars_enter_comment(upd, rem_ctx_insufficient)
        assert result == ConversationHandler.END

    async def test_insufficient_stars_no_update(self, rem_ctx_insufficient):
        repo = rem_ctx_insufficient.bot_data["sheet_repository"]
        upd = make_update(text="причина")
        await stars_enter_comment(upd, rem_ctx_insufficient)
        repo.sheet1.update_cell.assert_not_called()


# ---------------------------------------------------------------------------
# stars_preview_action — Отправить
# ---------------------------------------------------------------------------

class TestStarsPreviewActionConfirm:
    async def test_returns_end(self, preview_ctx, confirm_update):
        result = await stars_preview_action(confirm_update, preview_ctx)
        assert result == ConversationHandler.END

    async def test_notification_sent_to_teen(self, preview_ctx, confirm_update):
        await stars_preview_action(confirm_update, preview_ctx)
        send_calls = preview_ctx.bot.send_message.call_args_list
        teen_notified = any(
            "помогал убираться" in (c[1].get("text", "") or "")
            for c in send_calls
        )
        assert teen_notified

    async def test_stars_updated(self, preview_ctx, confirm_update):
        repo = preview_ctx.bot_data["sheet_repository"]
        await stars_preview_action(confirm_update, preview_ctx)
        # 10 + 5 = 15
        repo.sheet1.update_cell.assert_called_once_with(2, 7, "15")

    async def test_sheet2_logged(self, preview_ctx, confirm_update):
        repo = preview_ctx.bot_data["sheet_repository"]
        await stars_preview_action(confirm_update, preview_ctx)
        repo.add_comment_to_sheet2.assert_called_once_with(
            "111", "Пополнение", 5, "помогал убираться"
        )

    async def test_context_cleaned_up(self, preview_ctx, confirm_update):
        await stars_preview_action(confirm_update, preview_ctx)
        for key in ("selected_teen_id", "stars_amount", "operation",
                    "pending_comment", "pending_notification"):
            assert key not in preview_ctx.user_data


# ---------------------------------------------------------------------------
# stars_preview_action — Изменить комментарий
# ---------------------------------------------------------------------------

class TestStarsPreviewActionEdit:
    async def test_returns_enter_comment(self, preview_ctx, edit_update):
        result = await stars_preview_action(edit_update, preview_ctx)
        assert result == ENTER_COMMENT

    async def test_prompt_sent_to_admin(self, preview_ctx, edit_update):
        await stars_preview_action(edit_update, preview_ctx)
        preview_ctx.bot.send_message.assert_called_once()
        text = preview_ctx.bot.send_message.call_args[1]["text"]
        assert "комментарий" in text.lower()

    async def test_comment_message_id_saved(self, preview_ctx, edit_update):
        await stars_preview_action(edit_update, preview_ctx)
        assert "comment_message_id" in preview_ctx.user_data

    async def test_preview_message_deleted(self, preview_ctx, edit_update):
        await stars_preview_action(edit_update, preview_ctx)
        edit_update.callback_query.delete_message.assert_called_once()

    async def test_no_sheet_changes(self, preview_ctx, edit_update):
        repo = preview_ctx.bot_data["sheet_repository"]
        await stars_preview_action(edit_update, preview_ctx)
        repo.sheet1.update_cell.assert_not_called()
        repo.add_comment_to_sheet2.assert_not_called()


# ---------------------------------------------------------------------------
# _stars_process_operation — граничные случаи
# ---------------------------------------------------------------------------

class TestStarsProcessOperation:
    async def test_insufficient_stars_no_update(self):
        repo = make_sheet_repo(current_stars=2)
        ctx = make_context(
            user_data={"selected_teen_id": "111", "selected_teen_name": "Иван",
                       "stars_amount": 5, "operation": "rem"},
            sheet_repo=repo,
        )
        from tests.factories import make_message
        msg = make_message(chat_id=1)
        await _stars_process_operation(msg, ctx, "нарушение")
        repo.sheet1.update_cell.assert_not_called()

    async def test_insufficient_sends_error_message(self):
        repo = make_sheet_repo(current_stars=2)
        ctx = make_context(
            user_data={"selected_teen_id": "111", "selected_teen_name": "Иван",
                       "stars_amount": 5, "operation": "rem"},
            sheet_repo=repo,
        )
        from tests.factories import make_message
        msg = make_message(chat_id=1)
        await _stars_process_operation(msg, ctx, "нарушение")
        ctx.bot.send_message.assert_called_once()
        assert "Недостаточно" in ctx.bot.send_message.call_args[1]["text"]

    async def test_teen_not_found_ends(self):
        repo = make_sheet_repo()
        repo.sheet1.find.return_value = None
        ctx = make_context(
            user_data={"selected_teen_id": "999", "stars_amount": 3, "operation": "add"},
            sheet_repo=repo,
        )
        from tests.factories import make_message
        msg = make_message(chat_id=1)
        result = await _stars_process_operation(msg, ctx, "тест")
        assert result == ConversationHandler.END

    async def test_no_notification_on_remove(self):
        repo = make_sheet_repo(current_stars=10)
        ctx = make_context(
            user_data={"selected_teen_id": "111", "selected_teen_name": "Иван",
                       "stars_amount": 3, "operation": "rem",
                       "pending_notification": "уведомление"},
            sheet_repo=repo,
        )
        from tests.factories import make_message
        msg = make_message(chat_id=1)
        await _stars_process_operation(msg, ctx, "прогулял")
        teen_notified = any(
            "уведомление" in (c[1].get("text", "") or "")
            for c in ctx.bot.send_message.call_args_list
        )
        assert not teen_notified

    async def test_success_message_has_new_balance(self):
        repo = make_sheet_repo(current_stars=10)
        ctx = make_context(
            user_data={"selected_teen_id": "111", "selected_teen_name": "Иван",
                       "stars_amount": 3, "operation": "add",
                       "pending_notification": None},
            sheet_repo=repo,
        )
        from tests.factories import make_message
        msg = make_message(chat_id=1)
        await _stars_process_operation(msg, ctx, "помог")
        text = ctx.bot.send_message.call_args[1]["text"]
        assert "13" in text and "Успешно" in text
