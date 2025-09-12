#!/usr/bin/env python3
"""
Fixed import dengan better error handling dan timeout
Usage: python fixed_import.py drugs.csv
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import sys
import os
import time

def try_database_connection():
    """Try different connection configurations"""
    
    configs = [
        # Standard config
        {
            'host': 'localhost',
            'database': 'sadewa_db',
            'user': 'root',
            'password': '',
            'charset': 'utf8mb4',
            'connection_timeout': 3,
            'autocommit': True
        },
        # With IP address
        {
            'host': '127.0.0.1',
            'database': 'sadewa_db',
            'user': 'root',
            'password': '',
            'charset': 'utf8mb4',
            'connection_timeout': 3,
            'autocommit': True
        },
        # Different port
        {
            'host': 'localhost',
            'port': 3307,
            'database': 'sadewa_db',
            'user': 'root',
            'password': '',
            'charset': 'utf8mb4',
            'connection_timeout': 3,
            'autocommit': True
        }
    ]
    
    print("🔌 Testing database connections...")
    
    for i, config in enumerate(configs, 1):
        try:
            print(f"   Try {i}: {config['host']}:{config.get('port', 3306)}")
            
            start_time = time.time()
            connection = mysql.connector.connect(**config)
            end_time = time.time()
            
            if connection.is_connected():
                print(f"   ✅ Connected! ({end_time-start_time:.2f}s)")
                
                # Quick test
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM drugs")
                count = cursor.fetchone()[0]
                print(f"   📊 Drugs table: {count} records")
                
                cursor.close()
                return connection, config
                
        except Error as e:
            print(f"   ❌ Config {i} failed: {e}")
        except Exception as e:
            print(f"   ❌ Config {i} error: {e}")
    
    return None, None

def import_with_timeout(csv_file):
    """Import dengan connection timeout handling"""
    
    print("🚀 Fixed Drug Import")
    print("=" * 30)
    
    # Read CSV first
    try:
        print(f"📖 Reading CSV: {csv_file}")
        df = pd.read_csv(csv_file, sep=';', header=0, encoding='utf-8')
        print(f"   ✅ CSV loaded: {df.shape}")
        
        # Quick validation
        if len(df) == 0:
            print("   ❌ CSV is empty")
            return False
        
        columns = list(df.columns)
        print(f"   📊 Columns: {columns}")
        
    except Exception as e:
        print(f"   ❌ CSV error: {e}")
        return False
    
    # Connect to database
    connection, config = try_database_connection()
    
    if not connection:
        print("❌ All database connection attempts failed!")
        print("\n💡 Troubleshooting:")
        print("1. Check WAMP MySQL service (should be GREEN)")
        print("2. Try: mysql -u root -p")
        print("3. Check phpMyAdmin: http://localhost/phpmyadmin")
        return False
    
    try:
        print(f"\n🔄 Starting import process...")
        cursor = connection.cursor()
        
        # Get current count
        cursor.execute("SELECT COUNT(*) FROM drugs")
        before_count = cursor.fetchone()[0]
        print(f"   📊 Records before: {before_count}")
        
        # Auto-detect columns
        nama_obat_col = columns[0]  # Assuming first column is Indonesian
        nama_inter_col = columns[1]  # Assuming second column is International
        
        print(f"   📋 Using columns:")
        print(f"      Indonesian: '{nama_obat_col}'")
        print(f"      International: '{nama_inter_col}'")
        
        # Prepare insert query
        insert_query = """
        INSERT INTO drugs (nama_obat, nama_obat_internasional, is_active)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
        """
        
        # Process in batches for better performance
        batch_size = 50
        success_count = 0
        error_count = 0
        duplicate_count = 0
        
        print(f"   🔄 Processing {len(df)} records in batches of {batch_size}...")
        
        for batch_start in range(0, len(df), batch_size):
            batch_end = min(batch_start + batch_size, len(df))
            batch_df = df.iloc[batch_start:batch_end]
            
            print(f"      Batch {batch_start+1}-{batch_end}...")
            
            for index, row in batch_df.iterrows():
                try:
                    # Extract and clean data
                    nama_obat = str(row[nama_obat_col]).strip()
                    nama_inter = str(row[nama_inter_col]).strip()
                    
                    # Validate
                    if not nama_obat or not nama_inter or nama_obat == 'nan' or nama_inter == 'nan':
                        error_count += 1
                        continue
                    
                    if len(nama_obat) < 2 or len(nama_inter) < 2:
                        error_count += 1
                        continue
                    
                    # Insert
                    cursor.execute(insert_query, (nama_obat, nama_inter, True))
                    
                    if cursor.rowcount == 1:
                        success_count += 1
                    elif cursor.rowcount == 2:
                        duplicate_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:
                        print(f"         ❌ Row error: {e}")
            
            # Commit batch
            connection.commit()
            
            # Progress
            total_processed = batch_end
            print(f"      ✅ Processed: {total_processed}/{len(df)} (✅{success_count} 🔄{duplicate_count} ❌{error_count})")
        
        # Final stats
        cursor.execute("SELECT COUNT(*) FROM drugs")
        after_count = cursor.fetchone()[0]
        
        print(f"\n🎉 Import completed!")
        print(f"   ✅ New records: {success_count}")
        print(f"   🔄 Duplicates: {duplicate_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total in DB: {before_count} → {after_count}")
        
        # Sample new data
        print(f"\n📋 Sample imported drugs:")
        cursor.execute("""
            SELECT nama_obat, nama_obat_internasional 
            FROM drugs 
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        
        for i, (nama, inter) in enumerate(cursor.fetchall(), 1):
            print(f"   {i}. {nama} → {inter}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Import process error: {e}")
        if connection:
            connection.close()
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python fixed_import.py drugs.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    success = import_with_timeout(csv_file)
    
    if success:
        print(f"\n🎉 Import successful!")
        print(f"\n🚀 Test your API:")
        print(f"http://localhost:8000/api/drugs/stats")
        print(f"http://localhost:8000/api/drugs/search?q=para")
    else:
        print(f"\n💥 Import failed!")

if __name__ == "__main__":
    main()