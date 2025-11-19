# Как получить Connection Pooler String

## Проблема с Direct Connection

Direct connection (`db.gioxfhlmzewgtqspokrt.supabase.co`) использует **IPv6 только** и не работает из-за DNS проблем.

## Решение: Использовать Connection Pooler

В Supabase Dashboard есть два варианта Connection Pooler:

### 1. Session Pooler (для persistent connections)
- Порт: `5432`
- Формат: `postgres://postgres.[PROJECT_REF]:[PASSWORD]@[HOST]:5432/postgres`

### 2. Transaction Pooler (для serverless/edge functions)
- Порт: `6543`
- Формат: `postgres://postgres.[PROJECT_REF]:[PASSWORD]@[HOST]:6543/postgres`

## Где найти Connection Pooler String

1. Откройте: https://supabase.com/dashboard/project/gioxfhlmzewgtqspokrt
2. Нажмите **"Connect"** вверху страницы
3. Прокрутите вниз до раздела **"Connection Pooling"**
4. Найдите **"Session Pooler"** или **"Transaction Pooler"**
5. Скопируйте Connection String

## Что должно быть в Connection String

Пример формата:
```
postgres://postgres.gioxfhlmzewgtqspokrt:[PASSWORD]@[POOLER_HOST]:[PORT]/postgres
```

Где:
- `[POOLER_HOST]` - может быть `aws-0-[REGION].pooler.supabase.com` или другой формат
- `[PORT]` - `5432` (session) или `6543` (transaction)
- `[PASSWORD]` - ваш пароль `OExq0NAm6NDF04cQ`

## После получения Connection String

Извлеките из него:
- **Хост** (часть после `@` и до `:`)
- **Порт** (число после хоста)
- **Пользователь** (часть после `postgres://` и до `:`)

И обновите `.env`:
```env
SUPABASE_HOST=[POOLER_HOST]
SUPABASE_PORT=[PORT]
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
```

## Если не видите Connection Pooler

1. Убедитесь, что вы на странице **Connect** (не Settings)
2. Прокрутите вниз - Connection Pooling может быть ниже Direct Connection
3. Проверьте, что проект активен и не на паузе

