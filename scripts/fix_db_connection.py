#!/usr/bin/env python3
"""Script to fix and test PostgreSQL connection with correct Supabase format."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings
import asyncpg
from loguru import logger


async def test_connection_formats():
    """Test different connection formats."""
    settings = get_settings()
    project_ref = settings.supabase_url.split("//")[1].split(".")[0]
    
    print("\n" + "=" * 70)
    print("🔧 Testing Supabase Connection Formats")
    print("=" * 70)
    print(f"Project Ref: {project_ref}")
    print(f"Password: {'*' * len(settings.supabase_password) if settings.supabase_password else 'NOT SET'}")
    print()
    
    # Форматы для тестирования
    test_configs = [
        {
            "name": "Direct Connection (IPv6)",
            "host": f"db.{project_ref}.supabase.co",
            "port": 5432,
            "user": "postgres",
            "description": "Прямое подключение (требует IPv6)"
        },
        {
            "name": "Connection Pooler - Session Mode",
            "host": f"{project_ref}.pooler.supabase.com",
            "port": 5432,
            "user": f"postgres.{project_ref}",
            "description": "Session mode pooler (IPv4/IPv6)"
        },
        {
            "name": "Connection Pooler - Transaction Mode",
            "host": f"{project_ref}.pooler.supabase.com",
            "port": 6543,
            "user": f"postgres.{project_ref}",
            "description": "Transaction mode pooler (для serverless)"
        },
        {
            "name": "AWS Pooler - Session Mode",
            "host": f"aws-0-ap-southeast-1.pooler.supabase.com",
            "port": 5432,
            "user": f"postgres.{project_ref}",
            "description": "AWS pooler session mode"
        },
        {
            "name": "AWS Pooler - Transaction Mode",
            "host": f"aws-0-ap-southeast-1.pooler.supabase.com",
            "port": 6543,
            "user": f"postgres.{project_ref}",
            "description": "AWS pooler transaction mode"
        },
    ]
    
    working_config = None
    
    for config in test_configs:
        print(f"\n📡 Testing: {config['name']}")
        print(f"   Host: {config['host']}")
        print(f"   Port: {config['port']}")
        print(f"   User: {config['user']}")
        print(f"   Description: {config['description']}")
        
        try:
            # Попробовать подключиться
            conn = await asyncpg.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=settings.supabase_password,
                database=settings.supabase_db,
                ssl='require',
                timeout=10
            )
            
            # Выполнить тестовый запрос
            result = await conn.fetchval("SELECT version()")
            version_info = result.split(',')[0] if result else "Unknown"
            
            print(f"   ✅ SUCCESS! PostgreSQL: {version_info}")
            
            # Проверить таблицы
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            print(f"   📊 Found {len(tables)} tables:")
            for table in tables[:5]:
                print(f"      - {table['table_name']}")
            if len(tables) > 5:
                print(f"      ... and {len(tables) - 5} more")
            
            await conn.close()
            
            if not working_config:
                working_config = config
                print(f"\n   🎯 RECOMMENDED CONFIGURATION FOUND!")
            
        except Exception as e:
            error_msg = str(e)
            if "nodename" in error_msg.lower() or "dns" in error_msg.lower():
                print(f"   ❌ DNS resolution failed")
            elif "password" in error_msg.lower() or "authentication" in error_msg.lower():
                print(f"   ❌ Authentication failed (check password)")
            elif "timeout" in error_msg.lower():
                print(f"   ❌ Connection timeout")
            else:
                print(f"   ❌ Failed: {error_msg[:100]}")
    
    # Итоговые рекомендации
    print("\n" + "=" * 70)
    print("📋 RECOMMENDATIONS")
    print("=" * 70)
    
    if working_config:
        print("\n✅ WORKING CONFIGURATION:")
        print(f"\nAdd to your .env file:")
        print(f"SUPABASE_HOST={working_config['host']}")
        print(f"SUPABASE_PORT={working_config['port']}")
        print(f"SUPABASE_USER={working_config['user']}")
        print(f"\nCurrent .env has:")
        print(f"SUPABASE_HOST={settings.supabase_host}")
        print(f"SUPABASE_PORT={settings.supabase_port}")
        print(f"SUPABASE_USER={settings.supabase_user}")
        
        if (settings.supabase_host != working_config['host'] or 
            settings.supabase_port != working_config['port'] or
            settings.supabase_user != working_config['user']):
            print("\n⚠️  Configuration mismatch detected!")
            print("   Update .env file with the working configuration above.")
    else:
        print("\n❌ No working configuration found.")
        print("\nPossible solutions:")
        print("1. Check Supabase Dashboard → Settings → Database")
        print("   for the correct connection string")
        print("2. Verify your IP is allowed in Network Restrictions")
        print("3. Try using a VPN or different network")
        print("4. Check DNS settings (try Google DNS: 8.8.8.8)")
        print("5. Use REST API mode (already working)")
    
    print()


if __name__ == "__main__":
    asyncio.run(test_connection_formats())

