# Руководство по устранению проблем с подключением к PostgreSQL

## Текущая проблема

DNS не может разрешить хосты Supabase:
- `db.gioxfhlmzewgtqspokrt.supabase.co` - не разрешается
- `gioxfhlmzewgtqspokrt.pooler.supabase.com` - не разрешается

## Критические шаги для решения

### Шаг 1: Получить правильный Connection String из Supabase Dashboard

**ВАЖНО:** Это самый надежный способ получить правильные параметры подключения.

1. Откройте Supabase Dashboard: https://supabase.com/dashboard
2. Выберите проект `gioxfhlmzewgtqspokrt`
3. Перейдите в **Settings** → **Database**
4. Найдите раздел **Connection string** или **Connection pooling**
5. Скопируйте строку подключения

**Форматы подключения в Supabase:**

#### Direct Connection (IPv6 только)
```
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

#### Connection Pooler - Session Mode (IPv4/IPv6)
```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@[PROJECT_REF].pooler.supabase.com:5432/postgres
```

#### Connection Pooler - Transaction Mode (для serverless)
```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@[PROJECT_REF].pooler.supabase.com:6543/postgres
```

### Шаг 2: Обновить .env файл

После получения правильного connection string, обновите `.env`:

```env
# Для Connection Pooler (рекомендуется)
SUPABASE_HOST=gioxfhlmzewgtqspokrt.pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
SUPABASE_PASSWORD=XFsoh3Fj2EBjfQSW
SUPABASE_DB=postgres
```

Или для Session Mode:
```env
SUPABASE_HOST=gioxfhlmzewgtqspokrt.pooler.supabase.com
SUPABASE_PORT=5432
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
SUPABASE_PASSWORD=XFsoh3Fj2EBjfQSW
SUPABASE_DB=postgres
```

### Шаг 3: Проверить DNS настройки

Если DNS не работает, попробуйте использовать альтернативные DNS серверы:

**macOS:**
```bash
# Использовать Google DNS
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# Или Cloudflare DNS
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1

# Проверить разрешение
nslookup db.gioxfhlmzewgtqspokrt.supabase.co 8.8.8.8
```

**Linux:**
```bash
# Редактировать /etc/resolv.conf
sudo nano /etc/resolv.conf
# Добавить:
nameserver 8.8.8.8
nameserver 8.8.4.4
```

### Шаг 4: Проверить Network Restrictions в Supabase

1. Откройте Supabase Dashboard → Settings → Database
2. Найдите раздел **Network Restrictions**
3. Если включено "Restrict all access":
   - Добавьте ваш IP адрес: `109.196.195.29`
   - Или временно отключите ограничения для теста

### Шаг 5: Проверить SSL настройки

Supabase требует SSL для всех подключений. Код уже настроен на `ssl='require'`.

Если нужна проверка сертификата:
1. Скачайте сертификат из Supabase Dashboard → Settings → Database → SSL Configuration
2. Сохраните в `certs/supabase.crt`
3. Обновите код для использования сертификата

### Шаг 6: Тестирование подключения

После обновления `.env`:

```bash
# Запустить диагностику
python3 scripts/fix_db_connection.py

# Проверить подключение через приложение
python3 -m src.main admin test-connection

# Проверить работу dashboard
python3 -m src.main stats dashboard --period today
```

## Альтернативное решение: Использовать REST API

Если прямое подключение не работает, система автоматически использует REST API:
- ✅ Полностью функционально
- ✅ Не требует DNS разрешения
- ✅ Работает через HTTPS
- ✅ Уже работает в вашем проекте
- ⚠️ Немного медленнее для сложных запросов

## Автоматическое определение формата подключения

Код теперь автоматически определяет правильный формат пользователя для pooler подключений:
- Если хост содержит `pooler`, используется формат `postgres.[PROJECT_REF]`
- Для transaction mode (порт 6543) отключаются prepared statements

## Проверка текущей конфигурации

Текущие настройки в `.env`:
```env
SUPABASE_HOST=db.gioxfhlmzewgtqspokrt.supabase.co
SUPABASE_PORT=5432
SUPABASE_USER=postgres
```

**Рекомендуется изменить на:**
```env
SUPABASE_HOST=gioxfhlmzewgtqspokrt.pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_USER=postgres.gioxfhlmzewgtqspokrt
```

## Дополнительная диагностика

Если проблема сохраняется:

1. **Проверить доступность проекта:**
   ```bash
   curl https://gioxfhlmzewgtqspokrt.supabase.co/rest/v1/ -H "apikey: YOUR_KEY"
   ```

2. **Проверить DNS через разные серверы:**
   ```bash
   dig @8.8.8.8 db.gioxfhlmzewgtqspokrt.supabase.co
   dig @1.1.1.1 db.gioxfhlmzewgtqspokrt.supabase.co
   ```

3. **Проверить firewall:**
   ```bash
   # Проверить блокировку портов
   nc -zv db.gioxfhlmzewgtqspokrt.supabase.co 5432
   ```

4. **Использовать VPN** для проверки, не блокирует ли провайдер DNS запросы

## Контакты для поддержки

Если проблема не решается:
1. Обратитесь в поддержку Supabase: https://supabase.com/support
2. Укажите:
   - Project ID: `gioxfhlmzewgtqspokrt`
   - Ваш IP: `109.196.195.29`
   - Описание проблемы: DNS не разрешает хосты базы данных

