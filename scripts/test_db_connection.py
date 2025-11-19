#!/usr/bin/env python3
"""Test PostgreSQL connection with different configurations."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings
import asyncpg
from loguru import logger


async def test_direct_connection():
    """Test direct PostgreSQL connection."""
    settings = get_settings()
    
    print("\n" + "=" * 70)
    print("🔍 Testing Direct PostgreSQL Connection")
    print("=" * 70)
    print(f"Host: {settings.supabase_host}")
    print(f"Port: {settings.supabase_port}")
    print(f"User: {settings.supabase_user}")
    print(f"Database: {settings.supabase_db}")
    print()
    
    # Test 1: Without SSL
    print("Test 1: Connection without SSL...")
    try:
        conn = await asyncpg.connect(
            host=settings.supabase_host,
            port=settings.supabase_port,
            user=settings.supabase_user,
            password=settings.supabase_password,
            database=settings.supabase_db,
            timeout=10
        )
        result = await conn.fetchval("SELECT 1")
        print(f"✓ Connection successful! Result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 2: With SSL require
    print("\nTest 2: Connection with SSL='require'...")
    try:
        conn = await asyncpg.connect(
            host=settings.supabase_host,
            port=settings.supabase_port,
            user=settings.supabase_user,
            password=settings.supabase_password,
            database=settings.supabase_db,
            ssl='require',
            timeout=10
        )
        result = await conn.fetchval("SELECT 1")
        print(f"✓ Connection successful! Result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 3: With SSL context (no verification)
    print("\nTest 3: Connection with SSL context (no verification)...")
    try:
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        conn = await asyncpg.connect(
            host=settings.supabase_host,
            port=settings.supabase_port,
            user=settings.supabase_user,
            password=settings.supabase_password,
            database=settings.supabase_db,
            ssl=ssl_context,
            timeout=10
        )
        result = await conn.fetchval("SELECT 1")
        print(f"✓ Connection successful! Result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    return False


async def test_pooler_connection():
    """Test Connection Pooler connection."""
    settings = get_settings()
    
    # Extract project ID from URL
    project_id = settings.supabase_url.split("//")[1].split(".")[0]
    pooler_host = f"{project_id}.pooler.supabase.com"
    pooler_port = 6543  # Transaction mode
    # pooler_port = 5432  # Session mode
    
    print("\n" + "=" * 70)
    print("🔍 Testing Connection Pooler")
    print("=" * 70)
    print(f"Pooler Host: {pooler_host}")
    print(f"Pooler Port: {pooler_port} (Transaction mode)")
    print()
    
    # Test with pooler
    print("Test: Connection via Pooler...")
    try:
        conn = await asyncpg.connect(
            host=pooler_host,
            port=pooler_port,
            user=settings.supabase_user,
            password=settings.supabase_password,
            database=settings.supabase_db,
            ssl='require',
            timeout=10
        )
        result = await conn.fetchval("SELECT 1")
        print(f"✓ Pooler connection successful! Result: {result}")
        await conn.close()
        return True, pooler_host, pooler_port
    except Exception as e:
        print(f"✗ Pooler failed: {e}")
        return False, None, None


async def test_connection_strings():
    """Test different connection string formats."""
    settings = get_settings()
    
    print("\n" + "=" * 70)
    print("🔍 Testing Connection String Formats")
    print("=" * 70)
    
    # Extract project ID
    project_id = settings.supabase_url.split("//")[1].split(".")[0]
    
    formats = [
        {
            "name": "Direct connection",
            "host": settings.supabase_host,
            "port": settings.supabase_port,
        },
        {
            "name": "Connection Pooler (Transaction)",
            "host": f"{project_id}.pooler.supabase.com",
            "port": 6543,
        },
        {
            "name": "Connection Pooler (Session)",
            "host": f"{project_id}.pooler.supabase.com",
            "port": 5432,
        },
    ]
    
    for fmt in formats:
        print(f"\nTesting: {fmt['name']}")
        print(f"  Host: {fmt['host']}")
        print(f"  Port: {fmt['port']}")
        
        try:
            conn = await asyncpg.connect(
                host=fmt['host'],
                port=fmt['port'],
                user=settings.supabase_user,
                password=settings.supabase_password,
                database=settings.supabase_db,
                ssl='require',
                timeout=5
            )
            result = await conn.fetchval("SELECT version()")
            print(f"  ✓ Success! PostgreSQL version: {result[:50]}...")
            await conn.close()
            return fmt['host'], fmt['port']
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:100]}")
    
    return None, None


async def main():
    """Run all connection tests."""
    print("\n" + "=" * 70)
    print("🚀 PostgreSQL Connection Diagnostic Tool")
    print("=" * 70)
    
    # Test 1: Direct connection
    direct_success = await test_direct_connection()
    
    # Test 2: Pooler connection
    pooler_success, pooler_host, pooler_port = await test_pooler_connection()
    
    # Test 3: Try different formats
    working_host, working_port = await test_connection_strings()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"Direct connection: {'✓ Working' if direct_success else '✗ Failed'}")
    print(f"Pooler connection: {'✓ Working' if pooler_success else '✗ Failed'}")
    
    if working_host and working_port:
        print(f"\n✅ RECOMMENDED CONFIGURATION:")
        print(f"   SUPABASE_HOST={working_host}")
        print(f"   SUPABASE_PORT={working_port}")
        print(f"\n   Update your .env file with these values!")
    else:
        print("\n⚠️  No working configuration found.")
        print("   Possible issues:")
        print("   1. DNS resolution problem")
        print("   2. Network/firewall blocking")
        print("   3. Incorrect project ID")
        print("   4. SSL certificate required")
        print("\n   Check Supabase Dashboard → Settings → Database")
        print("   for the correct connection string.")


if __name__ == "__main__":
    asyncio.run(main())

