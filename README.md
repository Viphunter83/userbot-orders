# Userbot Orders

**Telegram userbot для мониторинга заказов с интеграцией Supabase и LLM-анализом**

Проект представляет собой асинхронный Telegram userbot, предназначенный для автоматического мониторинга заказов в Telegram-каналах. Бот использует Supabase для хранения данных, ProxyAPI для LLM-анализа сообщений и Pyrogram для работы с Telegram API. Система поддерживает структурированное логирование, экспорт данных и статистику по заказам.

---

**Telegram userbot for order monitoring with Supabase integration and LLM analysis**

This project is an asynchronous Telegram userbot designed for automatic order monitoring in Telegram channels. The bot uses Supabase for data storage, ProxyAPI for LLM-based message analysis, and Pyrogram for Telegram API interactions. The system supports structured logging, data export, and order statistics.

## Требования и запуск / Requirements and Setup

### Системные требования / System Requirements

- Python 3.10.11 или выше / Python 3.10.11 or higher
- Git
- Аккаунт Telegram с API credentials / Telegram account with API credentials
- Supabase проект / Supabase project
- API ключ для LLM провайдера / LLM provider API key

### Установка зависимостей / Install Dependencies

```bash
cd userbot-orders
pip install -r requirements.txt
```

### Настройка окружения / Environment Setup

1. Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Заполните переменные окружения в `.env`:
   - `TELEGRAM_API_ID` и `TELEGRAM_API_HASH` - получите на https://my.telegram.org/apps
   - `TELEGRAM_PHONE` - ваш номер телефона в формате +1234567890
   - `TELEGRAM_PASSWORD` - пароль 2FA (если включен)
   - `SUPABASE_URL` и `SUPABASE_KEY` - из вашего Supabase проекта
   - `LLM_API_KEY` - ключ API для ProxyAPI или другого LLM провайдера

### Проверка конфигурации / Verify Configuration

```bash
# Проверка загрузки настроек
python -m src.config.settings

# Проверка логирования
python -m src.utils.logger

# Запуск тестов
pytest
```

### Структура проекта / Project Structure

```
userbot-orders/
├── src/
│   ├── config/          # Конфигурация приложения
│   ├── telegram/        # Telegram client модули
│   ├── analysis/        # LLM анализ сообщений
│   ├── models/          # Модели данных
│   ├── database/        # Работа с Supabase
│   ├── export/          # Экспорт данных
│   ├── notifications/  # Уведомления
│   ├── stats/           # Статистика
│   └── utils/           # Утилиты (логирование и др.)
├── tests/               # Тесты
├── data/                # Данные (игнорируется git)
├── logs/                # Логи (игнорируется git)
├── .env                 # Переменные окружения (игнорируется git)
├── .env.example         # Пример конфигурации
├── requirements.txt     # Зависимости Python
└── README.md            # Документация
```

### Разработка / Development

Проект использует:
- **Pyrogram** для работы с Telegram API
- **Pydantic** для валидации настроек
- **Loguru** для структурированного логирования
- **pytest** для тестирования
- **asyncpg** и **SQLAlchemy** для работы с базой данных

### Лицензия / License

Проект находится в стадии разработки (MVP).

