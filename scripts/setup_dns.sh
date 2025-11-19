#!/bin/bash
# Скрипт для настройки альтернативных DNS серверов

set -e

echo "=========================================="
echo "Настройка альтернативных DNS серверов"
echo "=========================================="
echo ""

# Определить сетевой сервис
SERVICE=$(networksetup -listallnetworkservices | grep -E "(Wi-Fi|WiFi|Ethernet)" | head -1 | sed 's/^[0-9]*\. //')

if [ -z "$SERVICE" ]; then
    SERVICE="Wi-Fi"
    echo "⚠️  Не удалось определить сетевой сервис, используем: $SERVICE"
else
    echo "✅ Найден сетевой сервис: $SERVICE"
fi

echo ""
echo "Текущие DNS серверы:"
networksetup -getdnsservers "$SERVICE" || echo "  (не настроены)"

echo ""
echo "Настройка Google DNS (8.8.8.8, 8.8.4.4)..."
sudo networksetup -setdnsservers "$SERVICE" 8.8.8.8 8.8.4.4

echo ""
echo "✅ DNS серверы обновлены!"
echo ""
echo "Новые DNS серверы:"
networksetup -getdnsservers "$SERVICE"

echo ""
echo "Очистка DNS кеша..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

echo ""
echo "✅ DNS кеш очищен!"
echo ""
echo "Проверка разрешения хоста Supabase..."
nslookup db.gioxfhlmzewgtqspokrt.supabase.co 8.8.8.8 || echo "⚠️  Проверка не удалась"

echo ""
echo "=========================================="
echo "Настройка завершена!"
echo "=========================================="
echo ""
echo "Проверьте подключение:"
echo "  python3 -m src.main admin test-connection"

