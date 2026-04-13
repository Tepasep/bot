# bot-stars

Telegram-бот для управления звёздами (баллами) подростков. Хранение данных — Google Sheets.

## Функции

- Регистрация участников (`/start`)
- Просмотр баланса и рейтинга
- Вопросы администраторам
- Админ: начисление/списание звёзд с предпросмотром уведомления, блокировка, список участников

## Переменные окружения

```env
TELEGRAM_BOT_TOKEN=...
SPREADSHEET_NAME=Jesus Stars
CREDENTIALS_FILE=credentials.json
ADMIN_ID=111111111,222222222
```

## Запуск

```bash
pdm install
pdm run start
```

## Тесты

```bash
pdm run pytest
pdm run pytest --cov=bot_stars --cov-report=term-missing
```

Тесты не требуют реального подключения к Google Sheets — всё замокано.

## Docker

```bash
docker build -t bot-stars .

docker run --name bot-stars --env-file .env \
  -v "$(pwd)/credentials.json:/app/credentials.json:ro" \
  -e CREDENTIALS_FILE=/app/credentials.json \
  bot-stars
```

## CI/CD

- **push в main** — прогон тестов → деплой в Coolify
- **PR** — поднимается preview-окружение, при закрытии — останавливается
