# Руководство по подключению к Supabase PostgreSQL

## Текущий статус

✅ **Система работает через REST API** - это полностью функциональный режим для сохранения данных.

## Что уже настроено

- ✅ Database password добавлен в `.env`
- ✅ Конфигурация загружается корректно
- ✅ REST API подключение работает

## Проблема с прямым подключением

Хост `db.zyabiuahahndthqzyzne.supabase.co` не разрешается DNS. Это может быть связано с:
- Настройками сети/DNS
- Firewall блокирует разрешение имени
- Неправильным форматом хоста

## Что нужно для прямого подключения (опционально)

### 1. SSL Certificate

Если в настройках Supabase включен "Enforce SSL":
1. Нажмите "Download certificate" в разделе SSL Configuration
2. Сохраните файл (например: `certs/supabase.crt`)
3. Обновите код для использования SSL сертификата

### 2. Network Restrictions

Если включен "Restrict all access":
1. Добавьте ваш IP адрес в разрешенные
2. Или временно отключите ограничения для теста

**Ваш текущий IP:** (проверьте через `curl ifconfig.me`)

### 3. Connection Pooling URL

Попробуйте использовать Connection Pooling вместо прямого подключения:

```
Host: zyabiuahahndthqzyzne.pooler.supabase.com
Port: 6543
```

Или найдите правильный формат в Supabase Dashboard → Settings → Database → Connection string

## Рекомендация

**Для текущих задач (сохранение заказов) REST API режим полностью достаточен!**

Прямое подключение к PostgreSQL нужно только если:
- Нужны сложные SQL запросы
- Нужны транзакции
- Нужна максимальная производительность

## Проверка подключения

```bash
# Проверить текущее подключение
python -m src.database.base

# Должно показать:
# ✓ Database connection check: OK (via REST API)
```

## Альтернативные варианты

Если нужно прямое подключение, попробуйте:

1. **Использовать IP адрес напрямую** (если доступен в Supabase Dashboard)
2. **Проверить DNS настройки** вашей сети
3. **Использовать VPN** или другой DNS сервер
4. **Обратиться в поддержку Supabase** для проверки настроек проекта

## Текущая конфигурация

```env
SUPABASE_HOST=zyabiuahahndthqzyzne.pooler.supabase.com
SUPABASE_PORT=6543
SUPABASE_USER=postgres
SUPABASE_PASSWORD=XFsoh3Fj2EBjfQSW
SUPABASE_DB=postgres
```

Система автоматически переключается на REST API если прямое подключение недоступно.

