# Multi-stage build для оптимизации размера образа

# Stage 1: Build
FROM python:3.10.11-slim as builder

WORKDIR /app

# Установить зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копировать requirements
COPY requirements.txt .

# Установить Python пакеты в виртуальное окружение
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.10.11-slim

WORKDIR /app

# Установить только runtime зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копировать виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv

# Установить переменные окружения
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Копировать приложение
COPY src/ src/
COPY .env.example .env.example

# Создать user для безопасности
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from src.database.base import db_manager; asyncio.run(db_manager.initialize()); print('OK')" || exit 1

# Запустить приложение
CMD ["python", "-m", "src.main", "start"]

