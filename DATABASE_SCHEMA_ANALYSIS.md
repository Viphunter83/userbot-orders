# 🔍 Анализ соответствия структуры БД в Supabase проекту

**Дата:** 20 ноября 2025

---

## 📊 Сравнение SQL миграции и SQLAlchemy моделей

### ✅ Таблица: `chats`

| Поле | SQL миграция | SQLAlchemy модель | Статус |
|------|--------------|-------------------|--------|
| `id` | SERIAL PRIMARY KEY | Integer, primary_key=True | ✅ |
| `chat_id` | VARCHAR(50) UNIQUE NOT NULL | String(50), unique=True, nullable=False | ✅ |
| `chat_name` | VARCHAR(255) NOT NULL | String(255), nullable=False | ✅ |
| `chat_type` | VARCHAR(20) NOT NULL | String(20), nullable=False | ✅ |
| `is_active` | BOOLEAN NOT NULL DEFAULT TRUE | Boolean, default=True, nullable=False | ✅ |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | DateTime, default=datetime.utcnow | ⚠️ **TIMESTAMPTZ vs DateTime** |
| `last_message_at` | TIMESTAMPTZ | DateTime, nullable=True | ⚠️ **TIMESTAMPTZ vs DateTime** |

**Проблемы:**
- ⚠️ SQL использует `TIMESTAMPTZ` (timezone-aware), а SQLAlchemy использует `DateTime` (может быть naive)
- Это может привести к проблемам с timezone при работе с данными

---

### ✅ Таблица: `messages`

| Поле | SQL миграция | SQLAlchemy модель | Статус |
|------|--------------|-------------------|--------|
| `id` | SERIAL PRIMARY KEY | Integer, primary_key=True | ✅ |
| `message_id` | VARCHAR(50) NOT NULL | String(50), nullable=False | ✅ |
| `chat_id` | VARCHAR(50) NOT NULL REFERENCES chats(chat_id) | String(50), ForeignKey("chats.chat_id") | ✅ |
| `author_id` | VARCHAR(50) NOT NULL | String(50), nullable=False | ✅ |
| `author_name` | VARCHAR(255) | String(255), nullable=True | ✅ |
| `text` | TEXT NOT NULL | Text, nullable=False | ✅ |
| `timestamp` | TIMESTAMPTZ NOT NULL | DateTime, nullable=False | ⚠️ **TIMESTAMPTZ vs DateTime** |
| `processed` | BOOLEAN NOT NULL DEFAULT FALSE | Boolean, default=False, nullable=False | ✅ |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | DateTime, default=datetime.utcnow | ⚠️ **TIMESTAMPTZ vs DateTime** |

**Проблемы:**
- ⚠️ Тот же вопрос с timezone

**Индексы:**
- ✅ Все индексы соответствуют

---

### ⚠️ Таблица: `userbot_orders` (КРИТИЧНО!)

| Поле | SQL миграция | SQLAlchemy модель | Статус |
|------|--------------|-------------------|--------|
| `id` | SERIAL PRIMARY KEY | Integer, primary_key=True | ✅ |
| `message_id` | VARCHAR(50) UNIQUE NOT NULL | String(50), nullable=False, unique=True | ✅ |
| `chat_id` | VARCHAR(50) NOT NULL REFERENCES chats(chat_id) | String(50), ForeignKey("chats.chat_id") | ✅ |
| `author_id` | VARCHAR(50) NOT NULL | String(50), nullable=False | ✅ |
| `author_name` | VARCHAR(255) | String(255), nullable=True | ✅ |
| `text` | TEXT NOT NULL | Text, nullable=False | ✅ |
| `category` | VARCHAR(50) NOT NULL | String(50), nullable=False | ✅ |
| `relevance_score` | FLOAT NOT NULL CHECK (>= 0 AND <= 1) | Float, nullable=False | ⚠️ **Нет CHECK constraint в модели** |
| `detected_by` | VARCHAR(20) NOT NULL | String(20), nullable=False | ✅ |
| `telegram_link` | VARCHAR(500) | String(500), nullable=True | ✅ |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | DateTime, default=datetime.utcnow | ⚠️ **TIMESTAMPTZ vs DateTime** |
| `exported` | BOOLEAN NOT NULL DEFAULT FALSE | Boolean, default=False, nullable=False | ✅ |
| `feedback` | VARCHAR(20) | String(20), nullable=True | ✅ |
| `notes` | TEXT | Text, nullable=True | ✅ |

**Проблемы:**
- ⚠️ SQL имеет CHECK constraint на `relevance_score`, но SQLAlchemy модель не валидирует это
- ⚠️ Тот же вопрос с timezone

**Индексы:**
- ✅ Все индексы соответствуют

---

### ✅ Таблица: `stats`

| Поле | SQL миграция | SQLAlchemy модель | Статус |
|------|--------------|-------------------|--------|
| `id` | SERIAL PRIMARY KEY | Integer, primary_key=True | ✅ |
| `date` | VARCHAR(10) UNIQUE NOT NULL | String(10), unique=True, nullable=False | ✅ |
| `total_messages` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `detected_orders` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `regex_detections` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `llm_detections` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `llm_tokens_used` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `llm_cost` | FLOAT NOT NULL DEFAULT 0.0 | Float, default=0.0, nullable=False | ✅ |
| `avg_response_time_ms` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `false_positive_count` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | DateTime, default=datetime.utcnow | ⚠️ **TIMESTAMPTZ vs DateTime** |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | DateTime, default=datetime.utcnow, onupdate=datetime.utcnow | ⚠️ **TIMESTAMPTZ vs DateTime** |

**Проблемы:**
- ⚠️ Тот же вопрос с timezone

---

### ✅ Таблица: `chat_stats`

| Поле | SQL миграция | SQLAlchemy модель | Статус |
|------|--------------|-------------------|--------|
| `id` | SERIAL PRIMARY KEY | Integer, primary_key=True | ✅ |
| `chat_id` | VARCHAR(50) NOT NULL REFERENCES chats(chat_id) | String(50), ForeignKey("chats.chat_id") | ✅ |
| `date` | VARCHAR(10) NOT NULL | String(10), nullable=False | ✅ |
| `messages_count` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `orders_count` | INTEGER NOT NULL DEFAULT 0 | Integer, default=0, nullable=False | ✅ |
| `order_percentage` | FLOAT NOT NULL DEFAULT 0.0 | Float, default=0.0, nullable=False | ✅ |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | DateTime, default=datetime.utcnow | ⚠️ **TIMESTAMPTZ vs DateTime** |

**Проблемы:**
- ⚠️ Тот же вопрос с timezone

---

### ✅ Таблица: `feedback`

| Поле | SQL миграция | SQLAlchemy модель | Статус |
|------|--------------|-------------------|--------|
| `id` | SERIAL PRIMARY KEY | Integer, primary_key=True | ✅ |
| `order_id` | INTEGER NOT NULL REFERENCES userbot_orders(id) | Integer, ForeignKey("userbot_orders.id") | ✅ |
| `feedback_type` | VARCHAR(20) NOT NULL | String(20), nullable=False | ✅ |
| `reason` | VARCHAR(500) | String(500), nullable=True | ✅ |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | DateTime, default=datetime.utcnow | ⚠️ **TIMESTAMPTZ vs DateTime** |

**Проблемы:**
- ⚠️ Тот же вопрос с timezone

---

## 🔴 Критические проблемы

### 1. Timezone проблемы (TIMESTAMPTZ vs DateTime)

**Проблема:**
- SQL использует `TIMESTAMPTZ` (timezone-aware timestamps)
- SQLAlchemy использует `DateTime` (может быть naive или aware)
- Python `datetime.utcnow()` создает naive datetime (без timezone)

**Последствия:**
- Несоответствие типов при сохранении/чтении
- Проблемы с фильтрацией по датам
- Неправильное отображение времени

**Решение:**
- Использовать `datetime.now(timezone.utc)` вместо `datetime.utcnow()`
- Или использовать `DateTime(timezone=True)` в SQLAlchemy (если поддерживается)

### 2. Отсутствие CHECK constraint валидации

**Проблема:**
- SQL имеет CHECK constraint на `relevance_score` (0-1)
- SQLAlchemy модель не валидирует это на уровне приложения

**Последствия:**
- Возможны ошибки при вставке невалидных данных
- Ошибки будут обнаружены только в БД, а не в коде

**Решение:**
- Добавить валидацию в Pydantic модели
- Или добавить валидацию в SQLAlchemy через `CheckConstraint`

---

## ✅ Что работает корректно

1. ✅ Все таблицы соответствуют структуре
2. ✅ Все поля присутствуют и имеют правильные типы
3. ✅ Foreign keys настроены корректно
4. ✅ Индексы соответствуют
5. ✅ Unique constraints соответствуют

---

## 🎯 Рекомендации

### Немедленные действия:

1. **Исправить timezone проблемы:**
   ```python
   # В schemas.py заменить:
   from datetime import datetime, timezone
   
   created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
   ```

2. **Добавить валидацию relevance_score:**
   ```python
   from sqlalchemy import CheckConstraint
   
   relevance_score = Column(Float, CheckConstraint('relevance_score >= 0 AND relevance_score <= 1'), nullable=False)
   ```

### Долгосрочные улучшения:

3. **Добавить миграции Alembic:**
   - Для управления изменениями схемы
   - Для версионирования БД

4. **Добавить тесты схемы:**
   - Проверка соответствия моделей и БД
   - Автоматическая валидация

---

## 📝 Выводы

**Общий статус:** ⚠️ **Частичное соответствие**

**Основные проблемы:**
1. Timezone несоответствие (TIMESTAMPTZ vs DateTime)
2. Отсутствие валидации CHECK constraints в моделях

**Критичность:**
- Timezone проблемы могут привести к ошибкам при работе с датами
- Отсутствие валидации может привести к ошибкам при вставке данных

**Рекомендация:**
- Исправить timezone проблемы немедленно
- Добавить валидацию CHECK constraints
- Провести тестирование на реальных данных

---

**Версия:** 1.0  
**Дата:** 20 ноября 2025

