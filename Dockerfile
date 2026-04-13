ARG PYTHON_BASE=3.13-slim

FROM python:$PYTHON_BASE

# Устанавливаем инструменты для healthcheck на некоторых платформах
RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl ca-certificates \
	&& rm -rf /var/lib/apt/lists/*

# Устанавливаем PDM
RUN pip install -U pdm
ENV PDM_CHECK_UPDATE=false

# Создаем и переходим в рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml pdm.lock README.md /app/
COPY src/ /app/src

# Устанавливаем зависимости в виртуальное окружение PDM
RUN pdm install --check --prod --no-editable

ENV PATH="/app/.venv/bin:$PATH"

# Запускаем бота
ENTRYPOINT ["python", "-m", "bot_stars.main"]
