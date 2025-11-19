# Настройка Connection String для Supabase

## Текущая ситуация

✅ **Пароль настроен правильно** - `SUPABASE_PASSWORD` в `.env` читается корректно  
❌ **DNS не разрешает хосты** - это основная проблема

## Как получить правильный Connection String

### Шаг 1: Откройте Supabase Dashboard

1. Перейдите: https://supabase.com/dashboard/project/gioxfhlmzewgtqspokrt
2. Нажмите кнопку **"Connect"** в верхней части страницы
3. Или перейдите: **Settings** → **Database** → **Connection string**

### Шаг 2: Найдите Connection Pooling

В разделе **Connection pooling** вы увидите несколько вариантов:

#### Вариант 1: Transaction Mode (рекомендуется для вашего случая)
```
postgres://postgres.gioxfhlmzewgtqspokrt:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

#### Вариант 2: Session Mode
```
postgres://postgres.gioxfhlmzewgtqspokrt:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

**ВАЖНО:** Обратите внимание на:
- Формат хоста: `aws-0-[REGION].pooler.supabase.com` (не `gioxfhlmzewgtqspokrt.pooler.supabase.com`)
- Формат пользователя: `postgres.gioxfhlmzewgtqspokrt` (не просто `postgres`)
- Регион: может быть `ap-southeast-1`, `us-east-1`, `eu-west-1` и т.д.

### Шаг 3: Обновите .env файл

После получения правильного Connection String, обновите `.env`:

**Для Transaction Mode (порт 6543):**
```env
SUPABASE_HOST=aws-0-ap-southeast-1.pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
SUPABASE_PASSWORD=OExq0NAm6NDF04cQ
SUPABASE_DB=postgres
```

**Для Session Mode (порт 5432):**
```env
SUPABASE_HOST=aws-0-ap-southeast-1.pooler.supabase.com
SUPABASE_PORT=5432
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
SUPABASE_PASSWORD=OExq0NAm6NDF04cQ
SUPABASE_DB=postgres
```

**Замените `ap-southeast-1` на ваш регион из Connection String!**

### Шаг 4: Проверьте подключение

После обновления `.env`:

```bash
# Тест подключения
python3 scripts/fix_db_connection.py

# Или через приложение
python3 -m src.main admin test-connection
```

## Решение проблемы с DNS

Если DNS все еще не работает после обновления хоста:

### Вариант 1: Использовать Google DNS

```bash
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4
```

### Вариант 2: Использовать Cloudflare DNS

```bash
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1
```

### Вариант 3: Проверить через другой DNS

```bash
nslookup aws-0-ap-southeast-1.pooler.supabase.com 8.8.8.8
```

## Текущая конфигурация в .env

```env
SUPABASE_HOST=db.gioxfhlmzewgtqspokrt.supabase.co  # ❌ Неправильный формат
SUPABASE_PORT=5432
SUPABASE_USER=postgres  # ❌ Для pooler нужен postgres.gioxfhlmzewgtqspokrt
SUPABASE_PASSWORD=OExq0NAm6NDF04cQ  # ✅ Правильно
```

## Что нужно изменить

1. **Хост:** Заменить на формат `aws-0-[REGION].pooler.supabase.com`
2. **Пользователь:** Заменить на `postgres.gioxfhlmzewgtqspokrt`
3. **Порт:** Выбрать 6543 (transaction) или 5432 (session)

## Альтернатива: Использовать REST API

Если прямое подключение не работает, система автоматически использует REST API:
- ✅ Уже работает
- ✅ Не требует DNS
- ✅ Полностью функционально

