# Решение проблемы с DNS и Direct Connection

## Текущая ситуация

✅ **Пароль настроен правильно**  
✅ **Код готов к работе**  
❌ **DNS не разрешает хосты Supabase**  
❌ **Direct Connection требует IPv6, который не работает**

## Решение 1: Настроить альтернативные DNS (рекомендуется)

### macOS:

```bash
# Использовать Google DNS
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# Или Cloudflare DNS
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1

# Проверить настройки
networksetup -getdnsservers Wi-Fi
```

### После изменения DNS:

```bash
# Очистить DNS кеш
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Проверить разрешение
nslookup db.gioxfhlmzewgtqspokrt.supabase.co 8.8.8.8
```

## Решение 2: Использовать REST API (уже работает)

Система автоматически использует REST API когда прямое подключение недоступно:
- ✅ Полностью функционально
- ✅ Не требует DNS
- ✅ Работает через HTTPS
- ✅ Все команды работают

**Ничего менять не нужно** - система уже работает через REST API!

## Решение 3: Включить Connection Pooling в Supabase

Если Connection Pooling не виден в Dashboard:

1. Откройте: https://supabase.com/dashboard/project/gioxfhlmzewgtqspokrt/settings/database
2. Найдите раздел **"Connection Pooling"** или **"Supavisor"**
3. Убедитесь, что Connection Pooling включен
4. Если есть настройки, включите их

## Решение 4: Использовать VPN

Если DNS проблемы связаны с провайдером:
1. Подключитесь к VPN
2. Попробуйте подключиться снова

## Проверка после исправления DNS

После настройки альтернативных DNS:

```bash
# Проверить разрешение хоста
nslookup db.gioxfhlmzewgtqspokrt.supabase.co

# Проверить подключение
python3 -m src.main admin test-connection
```

## Текущая конфигурация (для Direct Connection)

Если DNS заработает, текущая конфигурация в `.env` правильная:

```env
SUPABASE_HOST=db.gioxfhlmzewgtqspokrt.supabase.co
SUPABASE_PORT=5432
SUPABASE_USER=postgres
SUPABASE_PASSWORD=OExq0NAm6NDF04cQ
SUPABASE_DB=postgres
```

## Рекомендация

**Для немедленной работы:** Система уже работает через REST API - ничего менять не нужно.

**Для прямого подключения:** Настройте альтернативные DNS (Google DNS или Cloudflare DNS) и перезапустите приложение.

