#!/usr/bin/env python3
"""
Debug version - Import drugs with detailed error handling
Usage: python debug_import.py drugs.csv
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'sadewa_db',
    'user': 'root',
    'password': '',  # Ubah jika ada password
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True
}

def test_mysql_connection():
    """Test MySQL connection tanpa database specific"""
    try:
        print("🔍 Testing MySQL connection...")
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        if connection.is_connected():
            print("✅ MySQL connection successful")
            
            # List databases
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print(f"📋 Available databases: {[db[0] for db in databases]}")
            
            # Check if sadewa_db exists
            db_exists = any('sadewa_db' in db for db in databases)
            if not db_exists:
                print("⚠️  Database 'sadewa_db' tidak ditemukan")
                print("📝 Creating database sadewa_db...")
                cursor.execute("CREATE DATABASE sadewa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print("✅ Database created successfully")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ MySQL connection error: {e}")
        return False

def create_drug_table():
    """Create drugs table if not exists"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS drugs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            nama_obat VARCHAR(255) NOT NULL,
            nama_obat_internasional VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_nama_obat (nama_obat),
            INDEX idx_nama_internasional (nama_obat_internasional),
            FULLTEXT KEY ft_drug_names (nama_obat, nama_obat_internasional),
            
            UNIQUE KEY unique_drug_names (nama_obat, nama_obat_internasional)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_table_query)
        print("✅ Table 'drugs' ready")
        
        # Check existing data
        cursor.execute("SELECT COUNT(*) FROM drugs")
        count = cursor.fetchone()[0]
        print(f"📊 Current drugs in database: {count}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Table creation error: {e}")
        return False

def analyze_csv_file(csv_file_path):
    """Analyze CSV file structure before import"""
    try:
        print(f"\n🔍 Analyzing CSV file: {csv_file_path}")
        
        # Try different encodings and separators
        encodings = ['utf-8', 'cp1252', 'iso-8859-1']
        separators = ['\t', ',', ';', '|',';']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(csv_file_path, sep=sep, encoding=encoding, nrows=5)
                    if len(df.columns) >= 2:
                        print(f"✅ Successfully read with encoding='{encoding}', separator='{sep}'")
                        print(f"📋 Columns found: {list(df.columns)}")
                        print(f"📊 Sample data:")
                        print(df.head(2))
                        return df, encoding, sep
                except Exception as e:
                    continue
        
        print("❌ Could not read CSV file with any encoding/separator combination")
        return None, None, None
        
    except Exception as e:
        print(f"❌ CSV analysis error: {e}")
        return None, None, None

def import_drugs_with_debug(csv_file_path):
    """Import dengan detailed debugging"""
    
    # Step 1: Test MySQL
    if not test_mysql_connection():
        return False
    
    # Step 2: Create table
    if not create_drug_table():
        return False
    
    # Step 3: Analyze CSV
    df_sample, encoding, separator = analyze_csv_file(csv_file_path)
    if df_sample is None:
        return False
    
    # Step 4: Identify columns
    columns = list(df_sample.columns)
    nama_obat_col = None
    nama_inter_col = None
    
    print(f"\n🔍 Looking for drug name columns...")
    for col in columns:
        col_lower = col.lower().strip()
        print(f"   - Column: '{col}' -> '{col_lower}'")
        
        if ('nama' in col_lower and 'obat' in col_lower and 'internasional' not in col_lower):
            nama_obat_col = col
            print(f"     ✅ Identified as Indonesian drug name")
        elif ('internasional' in col_lower or 'international' in col_lower):
            nama_inter_col = col
            print(f"     ✅ Identified as international drug name")
    
    if not nama_obat_col or not nama_inter_col:
        print(f"\n❌ Could not identify required columns!")
        print(f"Available columns: {columns}")
        print(f"Please ensure your CSV has columns containing:")
        print(f"- 'Nama Obat' (Indonesian name)")
        print(f"- 'Internasional' (International name)")
        return False
    
    print(f"\n✅ Column mapping:")
    print(f"   Indonesian: '{nama_obat_col}'")
    print(f"   International: '{nama_inter_col}'")
    
    # Step 5: Full import
    try:
        print(f"\n📖 Reading full CSV file...")
        df = pd.read_csv(csv_file_path, sep=separator, encoding=encoding)
        print(f"📊 Total records to process: {len(df)}")
        
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO drugs (nama_obat, nama_obat_internasional, is_active)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            updated_at = CURRENT_TIMESTAMP
        """
        
        success_count = 0
        error_count = 0
        duplicate_count = 0
        
        print(f"\n🔄 Processing records...")
        
        for index, row in df.iterrows():
            try:
                nama_obat = str(row[nama_obat_col]).strip() if pd.notna(row[nama_obat_col]) else None
                nama_inter = str(row[nama_inter_col]).strip() if pd.notna(row[nama_inter_col]) else None
                
                if not nama_obat or not nama_inter or nama_obat == 'nan' or nama_inter == 'nan':
                    error_count += 1
                    if index < 5:  # Show first few errors
                        print(f"   ⚠️  Row {index+1}: Empty values - '{nama_obat}' | '{nama_inter}'")
                    continue
                
                cursor.execute(insert_query, (nama_obat, nama_inter, True))
                
                if cursor.rowcount == 1:
                    success_count += 1
                elif cursor.rowcount == 2:
                    duplicate_count += 1
                
                # Progress indicator
                if (success_count + duplicate_count + error_count) % 100 == 0:
                    print(f"   📊 Processed: {success_count + duplicate_count + error_count}/{len(df)}")
                
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Show first few errors
                    print(f"   ❌ Row {index+1} error: {e}")
        
        connection.commit()
        
        print(f"\n🎉 Import completed!")
        print(f"   ✅ New records: {success_count}")
        print(f"   🔄 Duplicates: {duplicate_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total processed: {len(df)}")
        
        # Show sample
        cursor.execute("SELECT nama_obat, nama_obat_internasional FROM drugs ORDER BY created_at DESC LIMIT 5")
        samples = cursor.fetchall()
        print(f"\n📋 Sample imported drugs:")
        for sample in samples:
            print(f"   - {sample[0]} ({sample[1]})")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_import.py <csv_file>")
        print("Example: python debug_import.py drugs.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    print("🚀 SADEWA Drug Import Tool - Debug Edition")
    print("=" * 60)
    print(f"CSV File: {csv_file}")
    print(f"Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 60)
    
    success = import_drugs_with_debug(csv_file)
    
    if success:
        print(f"\n🎉 Import successful!")
        print(f"\nNext steps:")
        print(f"1. Test API: http://localhost:8000/api/drugs/stats")
        print(f"2. Search test: http://localhost:8000/api/drugs/search?q=para")
        print(f"3. Restart backend if needed")
    else:
        print(f"\n💥 Import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()