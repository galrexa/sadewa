#!/usr/bin/env python3
"""
Quick MySQL connection test
"""

import mysql.connector
from mysql.connector import Error
import time

def test_connection():
    print("🔍 Quick MySQL Connection Test")
    print("=" * 35)
    
    configs_to_try = [
        # Config 1: Standard WAMP
        {
            'host': 'localhost',
            'port': 3306,
            'database': 'sadewa_db',
            'user': 'root',
            'password': '',
            'connection_timeout': 5
        },
        # Config 2: With explicit port
        {
            'host': '127.0.0.1',
            'port': 3306,
            'database': 'sadewa_db',
            'user': 'root',
            'password': '',
            'connection_timeout': 5
        },
        # Config 3: No database specified
        {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'connection_timeout': 5
        }
    ]
    
    for i, config in enumerate(configs_to_try, 1):
        print(f"\n📊 Test {i}: {config}")
        
        try:
            start_time = time.time()
            connection = mysql.connector.connect(**config)
            end_time = time.time()
            
            if connection.is_connected():
                print(f"   ✅ Connected! ({end_time-start_time:.2f}s)")
                
                cursor = connection.cursor()
                
                # Test basic query
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print(f"   ✅ Query test: {result}")
                
                # Test database access if specified
                if 'database' in config:
                    cursor.execute("SELECT DATABASE()")
                    db = cursor.fetchone()
                    print(f"   ✅ Current DB: {db}")
                    
                    # Test drugs table
                    try:
                        cursor.execute("SELECT COUNT(*) FROM drugs")
                        count = cursor.fetchone()[0]
                        print(f"   ✅ Drugs table: {count} records")
                    except Exception as e:
                        print(f"   ⚠️  Drugs table: {e}")
                
                cursor.close()
                connection.close()
                print(f"   ✅ Connection closed properly")
                return True
                
        except Error as e:
            print(f"   ❌ MySQL Error: {e}")
        except Exception as e:
            print(f"   ❌ General Error: {e}")
    
    return False

def check_wamp_status():
    print("\n🔍 WAMP Troubleshooting Tips:")
    print("=" * 35)
    print("1. Check WAMP Control Panel:")
    print("   - Icon should be GREEN")
    print("   - MySQL service should be running")
    print()
    print("2. Check MySQL port:")
    print("   - Default: 3306")
    print("   - WAMP sometimes uses: 3307, 3308")
    print()
    print("3. Manual test in Command Prompt:")
    print("   mysql -u root -p")
    print("   (press Enter if no password)")
    print()
    print("4. Check phpMyAdmin:")
    print("   - http://localhost/phpmyadmin")
    print("   - Should show sadewa_db database")

if __name__ == "__main__":
    success = test_connection()
    
    if not success:
        check_wamp_status()
        print(f"\n💡 Try these solutions:")
        print(f"1. Restart WAMP MySQL service")
        print(f"2. Check if password is required")
        print(f"3. Try different port (3307, 3308)")
    else:
        print(f"\n🎉 MySQL connection working!")
        print(f"You can now run the import script")