# Исправление подключения к PostgreSQL

## Проблема

DNS не может разрешить хосты Supabase:
- `db.gioxfhlmzewgtqspokrt.supabase.co` - не разрешается
- `gioxfhlmzewgtqspokrt.pooler.supabase.com` - не разрешается

## Решения

### 1. Получить правильный Connection String из Supabase Dashboard

1. Откройте Supabase Dashboard: https://supabase.com/dashboard
2. Выберите проект `gioxfhlmzewgtqspokrt`
3. Перейдите в **Settings** → **Database**
4. Найдите раздел **Connection string**
5. Скопируйте строку подключения (URI или параметры)

### 2. Использовать Connection Pooling (рекомендуется)

Supabase предоставляет Connection Pooler для более стабильных подключений:

**Transaction Mode (рекомендуется для большинства случаев):**
```
Host: gioxfhlmzewgtqspokrt.pooler.supabase.com
Port: 6543
```

**Session Mode:**
```
Host: gioxfhlmzewgtqspokrt.pooler.supabase.com
Port: 5432
```

### 3. Проверить DNS настройки

Если DNS не работает, попробуйте:

```bash
# Использовать Google DNS
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# Или Cloudflare DNS
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1

# Проверить разрешение
nslookup db.gioxfhlmzewgtqspokrt.supabase.co 8.8.8.8
```

### 4. Использовать IP адрес напрямую (если доступен)

Если в Supabase Dashboard есть IP адрес базы данных, можно использовать его напрямую:

```env
SUPABASE_HOST=<IP_ADDRESS>
SUPABASE_PORT=5432
```

### 5. Проверить Network Restrictions в Supabase

1. Откройте Supabase Dashboard → Settings → Database
2. Проверьте раздел **Network Restrictions**
3. Если включено "Restrict all access", добавьте ваш IP адрес
4. Или временно отключите ограничения для теста

### 6. SSL Сертификат

Supabase требует SSL для всех подключений. Код уже настроен на использование `ssl='require'`.

Если нужна проверка сертификата:
1. Скачайте сертификат из Supabase Dashboard → Settings → Database → SSL Configuration
2. Сохраните в `certs/supabase.crt`
3. Обновите код для использования сертификата

## Текущая конфигурация

```env
SUPABASE_HOST=db.gioxfhlmzewgtqspokrt.supabase.co
SUPABASE_PORT=5432
SUPABASE_USER=postgres
SUPABASE_PASSWORD=XFsoh3Fj2EBjfQSW
SUPABASE_DB=postgres
```

## Рекомендуемая конфигурация (Connection Pooler)

```env
SUPABASE_HOST=gioxfhlmzewgtqspokrt.pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_USER=postgres
SUPABASE_PASSWORD=XFsoh3Fj2EBjfQSW
SUPABASE_DB=postgres
```

## Тестирование подключения

После обновления `.env` файла:

```bash
# Запустить диагностику
python3 scripts/test_db_connection.py

# Проверить подключение через приложение
python3 -m src.main admin test-connection
```

## Альтернатива: Использовать REST API

Если прямое подключение не работает, система автоматически использует REST API:
- ✅ Полностью функционально
- ✅ Не требует DNS разрешения
- ✅ Работает через HTTPS
- ⚠️ Немного медленнее для сложных запросов

