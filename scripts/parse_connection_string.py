#!/usr/bin/env python3
"""Parse Supabase Connection String and update .env file."""

import re
import sys
from pathlib import Path

def parse_connection_string(conn_str: str) -> dict:
    """
    Parse Supabase Connection String.
    
    Format: postgres://[user]:[password]@[host]:[port]/[database]
    """
    # Убрать пробелы и переносы строк
    conn_str = conn_str.strip()
    
    # Паттерн для парсинга
    pattern = r'postgres://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, conn_str)
    
    if not match:
        print("❌ Неверный формат Connection String")
        print("Ожидаемый формат: postgres://user:password@host:port/database")
        return None
    
    user, password, host, port, database = match.groups()
    
    return {
        'user': user,
        'host': host,
        'port': int(port),
        'database': database,
        'password': password  # Для проверки
    }


def update_env_file(env_path: Path, config: dict, dry_run: bool = False):
    """Update .env file with connection parameters."""
    if not env_path.exists():
        print(f"❌ Файл {env_path} не найден")
        return False
    
    # Читаем текущий .env
    lines = env_path.read_text().split('\n')
    
    # Обновляем параметры
    updated = False
    new_lines = []
    
    for line in lines:
        if line.startswith('SUPABASE_HOST='):
            new_lines.append(f"SUPABASE_HOST={config['host']}")
            updated = True
        elif line.startswith('SUPABASE_PORT='):
            new_lines.append(f"SUPABASE_PORT={config['port']}")
            updated = True
        elif line.startswith('SUPABASE_USER='):
            new_lines.append(f"SUPABASE_USER={config['user']}")
            updated = True
        elif line.startswith('SUPABASE_DB='):
            new_lines.append(f"SUPABASE_DB={config['database']}")
            updated = True
        else:
            new_lines.append(line)
    
    if dry_run:
        print("\n📝 Будет обновлено в .env:")
        print(f"   SUPABASE_HOST={config['host']}")
        print(f"   SUPABASE_PORT={config['port']}")
        print(f"   SUPABASE_USER={config['user']}")
        print(f"   SUPABASE_DB={config['database']}")
        return True
    
    # Записываем обратно
    env_path.write_text('\n'.join(new_lines))
    return updated


def main():
    """Main function."""
    print("=" * 70)
    print("🔧 Supabase Connection String Parser")
    print("=" * 70)
    print()
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 scripts/parse_connection_string.py 'postgres://user:pass@host:port/db'")
        print()
        print("Пример:")
        print("  python3 scripts/parse_connection_string.py 'postgres://postgres.gioxfhlmzewgtqspokrt:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres'")
        sys.exit(1)
    
    conn_str = sys.argv[1]
    
    # Парсим Connection String
    print(f"Парсинг Connection String...")
    config = parse_connection_string(conn_str)
    
    if not config:
        sys.exit(1)
    
    print("\n✅ Параметры извлечены:")
    print(f"   User: {config['user']}")
    print(f"   Host: {config['host']}")
    print(f"   Port: {config['port']}")
    print(f"   Database: {config['database']}")
    
    # Обновляем .env
    env_path = Path(__file__).parent.parent / '.env'
    
    print(f"\nОбновление {env_path}...")
    if update_env_file(env_path, config, dry_run=True):
        response = input("\nПрименить изменения? (y/n): ")
        if response.lower() == 'y':
            update_env_file(env_path, config, dry_run=False)
            print("\n✅ .env файл обновлен!")
            print("\nПроверьте подключение:")
            print("  python3 -m src.main admin test-connection")
        else:
            print("\nОтменено.")
    else:
        print("\n❌ Не удалось обновить .env файл")


if __name__ == "__main__":
    main()

