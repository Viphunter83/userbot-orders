# Быстрое решение проблемы с подключением

## ✅ Что уже правильно

1. **Пароль настроен правильно** - `SUPABASE_PASSWORD` в `.env` читается корректно
2. **Код готов** - автоматически определяет правильный формат для pooler

## ❌ Что нужно исправить

**Проблема:** Неправильный формат хоста в `.env`

### Текущие настройки (неправильные):
```env
SUPABASE_HOST=db.gioxfhlmzewgtqspokrt.supabase.co  # ❌ Неправильный формат
SUPABASE_USER=postgres  # ❌ Для pooler нужен другой формат
```

### Правильные настройки:

**ВАЖНО:** Нужно получить точный Connection String из Supabase Dashboard!

1. Откройте: https://supabase.com/dashboard/project/gioxfhlmzewgtqspokrt
2. Нажмите кнопку **"Connect"** вверху страницы
3. Найдите раздел **"Connection pooling"**
4. Скопируйте Connection String (формат будет примерно таким):

```
postgres://postgres.gioxfhlmzewgtqspokrt:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

5. Извлеките из него:
   - **Хост:** `aws-0-[REGION].pooler.supabase.com` (замените [REGION] на ваш регион)
   - **Порт:** `6543` (transaction mode) или `5432` (session mode)
   - **Пользователь:** `postgres.gioxfhlmzewgtqspokrt`

6. Обновите `.env`:

```env
SUPABASE_HOST=aws-0-[ВАШ_РЕГИОН].pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
SUPABASE_PASSWORD=OExq0NAm6NDF04cQ
SUPABASE_DB=postgres
```

## Примеры регионов

- `ap-southeast-1` - Singapore
- `us-east-1` - N. Virginia
- `eu-west-1` - Ireland
- `eu-central-1` - Frankfurt

**Замените `[ВАШ_РЕГИОН]` на регион из вашего Connection String!**

## После обновления

```bash
# Проверить подключение
python3 -m src.main admin test-connection

# Или запустить диагностику
python3 scripts/fix_db_connection.py
```

## Альтернатива

Если не можете получить Connection String, система продолжит работать через REST API (уже работает).

