"""
Общие pytest-фикстуры для всех тестов.
Фабрики для создания объектов находятся в tests/factories.py.
"""
import pytest
from tests.factories import make_context, make_sheet_repo, make_update, make_update_with_query


# ---------------------------------------------------------------------------
# Репозитории
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_male():
    """Репозиторий: подросток-мальчик, 10 звёзд."""
    return make_sheet_repo(current_stars=10, gender="Мужской")


@pytest.fixture
def repo_female():
    """Репозиторий: подросток-девочка, 5 звёзд."""
    return make_sheet_repo(current_stars=5, gender="Женский")


# ---------------------------------------------------------------------------
# Контексты для операции «добавление»
# ---------------------------------------------------------------------------

@pytest.fixture
def add_ctx(repo_male):
    return make_context(
        user_data={
            "selected_teen_id": "111",
            "selected_teen_name": "Иван Иванов",
            "stars_amount": 3,
            "operation": "add",
            "comment_message_id": 5,
        },
        sheet_repo=repo_male,
    )


@pytest.fixture
def add_ctx_female(repo_female):
    return make_context(
        user_data={
            "selected_teen_id": "222",
            "selected_teen_name": "Мария Петрова",
            "stars_amount": 2,
            "operation": "add",
            "comment_message_id": 5,
        },
        sheet_repo=repo_female,
    )


# ---------------------------------------------------------------------------
# Контексты для операции «списание»
# ---------------------------------------------------------------------------

@pytest.fixture
def rem_ctx(repo_male):
    return make_context(
        user_data={
            "selected_teen_id": "111",
            "selected_teen_name": "Иван Иванов",
            "stars_amount": 3,
            "operation": "rem",
            "comment_message_id": 5,
        },
        sheet_repo=repo_male,
    )


@pytest.fixture
def rem_ctx_insufficient(repo_male):
    """Списание больше, чем есть (10 звёзд, пытаемся снять 20)."""
    return make_context(
        user_data={
            "selected_teen_id": "111",
            "selected_teen_name": "Иван Иванов",
            "stars_amount": 20,
            "operation": "rem",
            "comment_message_id": 5,
        },
        sheet_repo=repo_male,
    )


# ---------------------------------------------------------------------------
# Контекст с готовым предпросмотром (для stars_preview_action)
# ---------------------------------------------------------------------------

@pytest.fixture
def preview_ctx(repo_male):
    return make_context(
        user_data={
            "selected_teen_id": "111",
            "selected_teen_name": "Иван Иванов",
            "stars_amount": 5,
            "operation": "add",
            "pending_comment": "помогал убираться",
            "pending_notification": "✨ Вау! Ты получил 5 звёзд за то, что ты помогал убираться! Красавчик!",
        },
        sheet_repo=repo_male,
    )


# ---------------------------------------------------------------------------
# Контекст для выбора подростка
# ---------------------------------------------------------------------------

@pytest.fixture
def selection_ctx(repo_male):
    return make_context(
        user_data={
            "operation": "add",
            "selection_message_id": 7,
            "selection_chat_id": 1,
        },
        sheet_repo=repo_male,
    )


# ---------------------------------------------------------------------------
# Простые Update / callback_query
# ---------------------------------------------------------------------------

@pytest.fixture
def comment_update():
    return make_update(text="помогал на служении")


@pytest.fixture
def confirm_update():
    return make_update_with_query(data="stars_confirm_send")


@pytest.fixture
def edit_update():
    return make_update_with_query(data="stars_edit_comment")
