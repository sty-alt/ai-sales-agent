# AI Sales Agent

Telegram-бот для настройки торгового агента, хранения клиентов и заявок, подготовки сообщений через Claude и просмотра статистики. Генератор лидов сейчас использует демонстрационный список имён и случайные номера: это не реальные контакты и не готовая система рассылки.

## Запуск

Нужны Python 3.11–3.12, токен Telegram-бота и ключ Anthropic API.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Заполните в `.env` значения `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_ID` и `CLAUDE_API_KEY`. Затем запустите бота из корня проекта:

```powershell
.\.venv\Scripts\python main.py
```

На Linux/macOS используйте `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`, `cp .env.example .env` и `python main.py`.

По умолчанию данные хранятся в локальной SQLite базе `ai_sales.db`. Файл `.env`, база данных и виртуальное окружение исключены из Git.

## Что есть в проекте

- `telegram_bot/` — команды и диалоги бота.
- `agents/` — генерация сообщений и фоновые задания.
- `leads/` — демонстрационные лиды.
- `database/` — модели SQLAlchemy.
- `payments/` — учёт счетов и подписок.
- `config/` — чтение настроек из окружения.

Платёжный модуль ведёт внутренние записи. Реального приёма платежей и автоматической проверки переводов в нём нет. Перед использованием с настоящими клиентами нужны собственный источник контактов, согласие на рассылку и проверка сценариев бота.
