# Пошаговая инструкция: Настройка Connection Pooler

## ✅ Что у вас уже есть

- ✅ Пароль: `OExq0NAm6NDF04cQ` (правильно настроен)
- ✅ Project Ref: `gioxfhlmzewgtqspokrt`
- ✅ Direct Connection String (но он IPv6 только и не работает)

## ❌ Что нужно найти

В Supabase Dashboard нужно найти **Connection Pooler** строки (они отличаются от Direct Connection).

## 📋 Пошаговая инструкция

### Шаг 1: Откройте страницу Connect

1. Перейдите: https://supabase.com/dashboard/project/gioxfhlmzewgtqspokrt
2. Нажмите кнопку **"Connect"** в верхней части страницы (рядом с "Settings")

### Шаг 2: Найдите раздел Connection Pooling

На странице Connect вы увидите несколько разделов:

1. **Direct Connection** (это вы уже видели - IPv6 только)
2. **Connection Pooling** ← **ЭТОТ РАЗДЕЛ НУЖЕН!**

Прокрутите вниз от Direct Connection - там должен быть раздел **"Connection Pooling"** или **"Supavisor"**.

### Шаг 3: Найдите Connection Strings

В разделе Connection Pooling должны быть два варианта:

#### Вариант A: Transaction Mode
```
postgres://postgres.gioxfhlmzewgtqspokrt:[YOUR-PASSWORD]@[HOST]:6543/postgres
```

#### Вариант B: Session Mode  
```
postgres://postgres.gioxfhlmzewgtqspokrt:[YOUR-PASSWORD]@[HOST]:5432/postgres
```

**ВАЖНО:** Обратите внимание на:
- **Хост** - это будет что-то вроде `aws-0-[REGION].pooler.supabase.com` или другой формат
- **Порт** - `6543` (transaction) или `5432` (session)
- **Пользователь** - `postgres.gioxfhlmzewgtqspokrt`

### Шаг 4: Скопируйте Connection String

Скопируйте **полный** Connection String из одного из вариантов (рекомендуется Transaction Mode).

### Шаг 5: Извлеките параметры

Из Connection String извлеките:
- **Хост** (часть между `@` и `:`)
- **Порт** (число после хоста)
- **Пользователь** (часть между `postgres://` и `:`)

### Шаг 6: Обновите .env

Обновите файл `.env`:

```env
SUPABASE_HOST=[ХОСТ_ИЗ_CONNECTION_STRING]
SUPABASE_PORT=[ПОРТ_ИЗ_CONNECTION_STRING]
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
SUPABASE_PASSWORD=OExq0NAm6NDF04cQ
SUPABASE_DB=postgres
```

**Пример:**
Если Connection String:
```
postgres://postgres.gioxfhlmzewgtqspokrt:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

То в `.env`:
```env
SUPABASE_HOST=aws-0-us-east-1.pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
```

### Шаг 7: Проверьте подключение

```bash
python3 -m src.main admin test-connection
```

## 🔍 Если не видите Connection Pooling

1. Убедитесь, что вы на странице **Connect** (не Settings → Database)
2. Прокрутите страницу вниз - Connection Pooling может быть ниже
3. Проверьте, что проект активен (не на паузе)
4. Попробуйте обновить страницу

## 💡 Альтернатива

Если Connection Pooling недоступен, система продолжит работать через REST API (уже работает).

