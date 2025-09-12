#!/usr/bin/env python3
"""
Script sederhana untuk import data obat Fornas dari CSV ke MySQL database
Usage: python import_drugs.py drugs.csv
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime

# Database configuration - sesuaikan dengan setup Anda
DB_CONFIG = {
    'host': 'localhost',
    'database': 'sadewa_db',  # Ganti dengan nama database Anda
    'user': 'root',
    'password': '',  # Ganti dengan password MySQL Anda
    'charset': 'utf8mb4',
    'use_unicode': True
}

def create_connection():
    """Membuat koneksi ke MySQL database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print(f"✅ Connected to MySQL database: {DB_CONFIG['database']}")
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def clean_drug_name(name):
    """Clean and standardize drug names"""
    if pd.isna(name) or name == '':
        return None
    
    # Remove extra whitespace
    cleaned = str(name).strip()
    return cleaned if cleaned else None

def import_drugs_from_csv(csv_file_path):
    """Import drugs data from CSV file"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ File tidak ditemukan: {csv_file_path}")
        return False
    
    connection = create_connection()
    if not connection:
        return False
    
    try:
        # Read CSV file - coba beberapa separator
        print(f"📖 Reading CSV file: {csv_file_path}")
        
        # Coba tab-separated dulu
        try:
            df = pd.read_csv(csv_file_path, sep='\t', encoding='utf-8')
        except:
            # Kalau gagal, coba comma-separated
            try:
                df = pd.read_csv(csv_file_path, sep=';', encoding='utf-8')
            except:
                # Kalau masih gagal, coba encoding windows
                df = pd.read_csv(csv_file_path, sep='\t', encoding='cp1252')
        
        print(f"📊 Kolom yang ditemukan: {list(df.columns)}")
        print(f"📊 Total records: {len(df)}")
        
        # Validate columns - nama kolom bisa bervariasi
        nama_obat_col = None
        nama_inter_col = None
        
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'nama obat' in col_lower and 'internasional' not in col_lower:
                nama_obat_col = col
            elif 'internasional' in col_lower or 'international' in col_lower:
                nama_inter_col = col
        
        if not nama_obat_col or not nama_inter_col:
            print(f"❌ Kolom yang diperlukan tidak ditemukan!")
            print(f"Perlu kolom yang mengandung: 'Nama Obat' dan 'Internasional'")
            print(f"Kolom tersedia: {list(df.columns)}")
            return False
        
        print(f"✅ Menggunakan kolom:")
        print(f"   - Nama Obat: '{nama_obat_col}'")
        print(f"   - Nama Internasional: '{nama_inter_col}'")
        
        cursor = connection.cursor()
        
        # Prepare insert statement
        insert_query = """
        INSERT INTO drugs (nama_obat, nama_obat_internasional, is_active)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            updated_at = CURRENT_TIMESTAMP
        """
        
        success_count = 0
        error_count = 0
        duplicate_count = 0
        
        print("🔄 Processing records...")
        
        for index, row in df.iterrows():
            try:
                nama_obat = clean_drug_name(row[nama_obat_col])
                nama_obat_internasional = clean_drug_name(row[nama_inter_col])
                
                # Skip if either name is empty
                if not nama_obat or not nama_obat_internasional:
                    print(f"⚠️  Skipping row {index+1}: Empty drug name")
                    error_count += 1
                    continue
                
                # Skip jika sama (duplikasi dalam satu row)
                if nama_obat.lower() == nama_obat_internasional.lower():
                    # Gunakan nama obat sebagai keduanya
                    pass
                
                # Execute insert
                cursor.execute(insert_query, (
                    nama_obat,
                    nama_obat_internasional,
                    True  # is_active
                ))
                
                # Check if it was actually inserted or just updated
                if cursor.rowcount == 1:
                    success_count += 1
                elif cursor.rowcount == 2:  # ON DUPLICATE KEY UPDATE
                    duplicate_count += 1
                
                if (success_count + duplicate_count) % 100 == 0:
                    print(f"✅ Processed {success_count + duplicate_count} records...")
                    
            except Exception as e:
                print(f"❌ Error processing row {index+1}: {e}")
                print(f"   Row data: {nama_obat} | {nama_obat_internasional}")
                error_count += 1
                continue
        
        # Commit changes
        connection.commit()
        
        print(f"\n📊 Import Summary:")
        print(f"   ✅ Successfully imported: {success_count} records")
        print(f"   🔄 Duplicates updated: {duplicate_count} records")
        print(f"   ❌ Errors: {error_count} records")
        print(f"   📝 Total processed: {len(df)} records")
        
        # Show current database stats
        cursor.execute("SELECT COUNT(*) FROM drugs WHERE is_active = TRUE")
        total_drugs = cursor.fetchone()[0]
        print(f"   📋 Total drugs in database: {total_drugs}")
        
        # Show sample imported records
        print(f"\n📋 Sample records in database:")
        cursor.execute("""
            SELECT nama_obat, nama_obat_internasional 
            FROM drugs 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        for record in cursor.fetchall():
            print(f"   - {record[0]} ({record[1]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        return False
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Database connection closed")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python import_drugs.py <csv_file_path>")
        print("Example: python import_drugs.py fornas_drugs.csv")
        print("\nFile CSV harus berisi kolom:")
        print("- Nama Obat (atau yang mengandung kata 'nama obat')")
        print("- Nama Obat Internasional (atau yang mengandung kata 'internasional')")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("🚀 SADEWA Drug Import Tool - Fornas Edition")
    print("=" * 60)
    print(f"CSV File: {csv_file}")
    print(f"Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 60)
    
    success = import_drugs_from_csv(csv_file)
    
    if success:
        print("\n🎉 Import completed successfully!")
        print("\nNext steps:")
        print("1. Restart backend server untuk load data terbaru")
        print("2. Test drug search di frontend")
        print("3. Add interaction data jika diperlukan")
    else:
        print("\n💥 Import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()