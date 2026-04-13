import sys
import os
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import bot_stars.commands as commands_module
from bot_stars.commands import MENU_BUTTON_TEXTS, handle_menu, is_menu_command_text
from bot_stars.commands import cleanup_incomplete_action_messages
from tests.factories import make_context, make_update


def test_menu_button_texts_contains_common_actions():
    assert "💫 Мой баланс" in MENU_BUTTON_TEXTS
    assert "❓ Задать вопрос" in MENU_BUTTON_TEXTS
    assert "📝 Активные вопросы" in MENU_BUTTON_TEXTS


def test_is_menu_command_text_returns_true_for_menu_buttons():
    assert is_menu_command_text("💫 Мой баланс") is True
    assert is_menu_command_text("📝 Активные вопросы") is True


def test_is_menu_command_text_returns_false_for_regular_text():
    assert is_menu_command_text("Привет") is False
    assert is_menu_command_text("") is False
    assert is_menu_command_text(None) is False


async def test_cleanup_incomplete_action_messages_deletes_selection_message():
    context = make_context(
        user_data={
            "selection_chat_id": 1,
            "selection_message_id": 77,
        }
    )
    update = make_update(text="⭐️ Убрать звезды", chat_id=1)

    await cleanup_incomplete_action_messages(update, context)

    context.bot.delete_message.assert_awaited_once_with(chat_id=1, message_id=77)


async def test_cleanup_incomplete_action_messages_deletes_step_messages_in_current_chat():
    context = make_context(
        user_data={
            "stars_message_id": 10,
            "comment_message_id": 20,
            "preview_message_id": 30,
        }
    )
    update = make_update(text="💫 Мой баланс", chat_id=5)

    await cleanup_incomplete_action_messages(update, context)

    calls = context.bot.delete_message.await_args_list
    assert len(calls) == 3
    assert calls[0].kwargs == {"chat_id": 5, "message_id": 10}
    assert calls[1].kwargs == {"chat_id": 5, "message_id": 20}
    assert calls[2].kwargs == {"chat_id": 5, "message_id": 30}


async def test_cleanup_incomplete_action_messages_deletes_generic_action_message():
    context = make_context(
        user_data={
            "action_chat_id": 8,
            "action_message_id": 42,
        }
    )
    update = make_update(text="🚫 Разблокировать пользователя", chat_id=8)

    await cleanup_incomplete_action_messages(update, context)

    context.bot.delete_message.assert_awaited_once_with(chat_id=8, message_id=42)


@pytest.mark.asyncio
async def test_handle_menu_calls_cleanup_before_dispatch(monkeypatch):
    update = make_update(text="💫 Мой баланс", chat_id=11)
    context = make_context(user_data={"action_chat_id": 11, "action_message_id": 55})

    cleanup_mock = AsyncMock()
    viewstars_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(commands_module, "cleanup_incomplete_action_messages", cleanup_mock)
    monkeypatch.setattr(commands_module, "viewstars", viewstars_mock)

    await handle_menu(update, context)

    cleanup_mock.assert_awaited_once_with(update, context)
    viewstars_mock.assert_awaited_once_with(update, context)
