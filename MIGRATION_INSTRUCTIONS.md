# Инструкция по созданию таблиц в проекте gioxfhlmzewgtqspokrt

## Шаг 1: Откройте Supabase Dashboard

1. Перейдите на https://supabase.com/dashboard
2. Выберите проект **gioxfhlmzewgtqspokrt**

## Шаг 2: Откройте SQL Editor

1. В левом меню нажмите на **SQL Editor**
2. Нажмите **New query**

## Шаг 3: Выполните миграцию

1. Откройте файл `migration_gioxfhlmzewgtqspokrt.sql` в этом проекте
2. Скопируйте весь SQL код
3. Вставьте в SQL Editor в Supabase Dashboard
4. Нажмите **Run** (или `Ctrl+Enter` / `Cmd+Enter`)

## Шаг 4: Проверка

После выполнения миграции вы должны увидеть результат запроса в конце файла:

```
table_name
-----------
chat_stats
chats
feedback
messages
stats
userbot_orders
```

Все 6 таблиц должны быть созданы.

## Альтернативный способ: Table Editor

Если предпочитаете создавать таблицы вручную:

1. Перейдите в **Table Editor**
2. Нажмите **New table**
3. Создайте каждую таблицу согласно схеме из `migration_gioxfhlmzewgtqspokrt.sql`

## Что будет создано

1. **chats** - отслеживаемые Telegram-чаты
2. **messages** - все сообщения из чатов
3. **userbot_orders** - обнаруженные заказы
4. **stats** - ежедневная статистика
5. **chat_stats** - статистика по чатам
6. **feedback** - feedback от оператора

## После создания таблиц

Обновите ваш JavaScript код:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://gioxfhlmzewgtqspokrt.supabase.co'
const supabaseKey = process.env.SUPABASE_KEY

const supabase = createClient(supabaseUrl, supabaseKey)
```

Теперь вы можете использовать эти таблицы в вашем приложении!

