# Настройка Supabase для userbot-orders

## Текущий проект

**Project ID:** `zyabiuahahndthqzyzne`  
**URL:** `https://zyabiuahahndthqzyzne.supabase.co`

## Созданные таблицы

Все таблицы успешно созданы в проекте:

1. ✅ `chats` - отслеживаемые Telegram-чаты
2. ✅ `messages` - все сообщения из чатов
3. ✅ `userbot_orders` - обнаруженные заказы
4. ✅ `stats` - ежедневная статистика
5. ✅ `chat_stats` - статистика по чатам
6. ✅ `feedback` - feedback от оператора

## Использование в JavaScript/TypeScript

Если вы используете Supabase клиент в другом проекте, используйте правильный URL:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://zyabiuahahndthqzyzne.supabase.co'
const supabaseKey = process.env.SUPABASE_KEY // или ваш anon key

const supabase = createClient(supabaseUrl, supabaseKey)
```

## Проверка таблиц

Вы можете проверить таблицы через Supabase Dashboard:
- Перейдите в Table Editor
- Должны быть видны все 6 таблиц

Или через SQL:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('chats', 'messages', 'userbot_orders', 'stats', 'chat_stats', 'feedback')
ORDER BY table_name;
```

## Если нужен другой проект

Если вам нужен проект `gioxfhlmzewgtqspokrt`, нужно:
1. Создать таблицы в том проекте (используя миграцию)
2. Или использовать правильный проект `zyabiuahahndthqzyzne`
