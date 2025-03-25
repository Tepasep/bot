FROM python:3.11-slim

# Устанавливаем PDM
RUN pip install pdm

# Создаем и переходим в рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml pdm.lock /app/

# Устанавливаем зависимости в виртуальное окружение PDM
RUN pdm install --prod

# Копируем код бота
COPY . /app

# Запускаем бота
ENTRYPOINT ["pdm", "run", "start"]
