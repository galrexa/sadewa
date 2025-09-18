#!/usr/bin/env python3
"""
Script sederhana untuk import CSV obat Fornas ke MySQL
Usage: python fixed_import.py drugs.csv
"""

import csv
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
    'password': '',  # Sesuaikan dengan password MySQL Anda
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': False  # Manual commit untuk better control
}

def test_connection():
    """Test koneksi database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM drugs")
            count = cursor.fetchone()[0]
            print(f"✅ Database connected. Current drugs: {count}")
            cursor.close()
            connection.close()
            return True
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return False

def read_csv_file(csv_file_path):
    """Baca CSV file dengan berbagai format"""
    if not os.path.exists(csv_file_path):
        print(f"❌ File tidak ditemukan: {csv_file_path}")
        return None
    
    print(f"📖 Reading CSV: {csv_file_path}")
    
    # Coba berbagai delimiter dan encoding
    configs = [
        {'delimiter': ';', 'encoding': 'utf-8'},
        {'delimiter': '\t', 'encoding': 'utf-8'},
        {'delimiter': ',', 'encoding': 'utf-8'},
        {'delimiter': ';', 'encoding': 'cp1252'},
        {'delimiter': ';', 'encoding': 'iso-8859-1'}
    ]
    
    for config in configs:
        try:
            drugs = []
            with open(csv_file_path, 'r', encoding=config['encoding']) as file:
                reader = csv.reader(file, delimiter=config['delimiter'])
                
                # Skip header jika ada
                first_row = next(reader, None)
                if first_row and len(first_row) >= 2:
                    # Check if first row looks like header
                    if 'nama' in first_row[0].lower() or 'drug' in first_row[0].lower():
                        print(f"   📋 Skipping header: {first_row}")
                    else:
                        # First row is data
                        drugs.append(first_row)
                
                # Read all rows
                for row in reader:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        drugs.append(row)
                
                if len(drugs) > 0:
                    print(f"   ✅ Success with {config}: {len(drugs)} rows")
                    return drugs
                    
        except Exception as e:
            print(f"   ❌ Failed with {config}: {e}")
            continue
    
    return None

def clean_drug_name(name):
    """Clean drug name"""
    if not name or not name.strip():
        return None
    return name.strip()[:250]  # Limit to 250 chars

def import_drugs_to_database(drugs_data):
    """Import drugs ke database"""
    if not drugs_data:
        print("❌ No data to import")
        return False
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print(f"🔄 Starting import of {len(drugs_data)} records...")
        
        # Prepare query dengan ON DUPLICATE KEY UPDATE
        insert_query = """
        INSERT INTO drugs (nama_obat, nama_obat_internasional, is_active)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            updated_at = CURRENT_TIMESTAMP,
            is_active = VALUES(is_active)
        """
        
        success_count = 0
        error_count = 0
        
        # Process in batches
        batch_size = 50
        for i in range(0, len(drugs_data), batch_size):
            batch = drugs_data[i:i + batch_size]
            batch_data = []
            
            for row in batch:
                if len(row) >= 2:
                    nama_obat = clean_drug_name(row[0])
                    nama_inter = clean_drug_name(row[1])
                    
                    if nama_obat and nama_inter:
                        batch_data.append((nama_obat, nama_inter, True))
                    else:
                        error_count += 1
                else:
                    error_count += 1
            
            # Execute batch
            if batch_data:
                try:
                    cursor.executemany(insert_query, batch_data)
                    connection.commit()
                    success_count += len(batch_data)
                    print(f"   ✅ Batch {i//batch_size + 1}: {len(batch_data)} records")
                except Error as e:
                    print(f"   ❌ Batch {i//batch_size + 1} error: {e}")
                    connection.rollback()
                    error_count += len(batch_data)
        
        # Final stats
        cursor.execute("SELECT COUNT(*) FROM drugs WHERE is_active = 1")
        total_count = cursor.fetchone()[0]
        
        print(f"\n📊 Import Summary:")
        print(f"   ✅ Successfully imported: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📈 Total drugs in database: {total_count}")
        
        # Show sample data
        cursor.execute("""
            SELECT nama_obat, nama_obat_internasional 
            FROM drugs 
            WHERE is_active = 1
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        if samples:
            print(f"\n📋 Sample imported drugs:")
            for sample in samples:
                print(f"   - {sample[0]} ({sample[1]})")
        
        cursor.close()
        connection.close()
        return success_count > 0
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 SADEWA Drug Import Tool - Fixed Version")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print("-" * 60)
    
    # Check arguments
    if len(sys.argv) != 2:
        print("❌ Usage: python fixed_import.py <csv_file_path>")
        print("Example: python fixed_import.py drugs.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Step 1: Test database connection
    print("1️⃣ Testing database connection...")
    if not test_connection():
        print("💡 Troubleshooting:")
        print("   - Check WAMP/XAMPP MySQL service is running")
        print("   - Verify database 'sadewa_db' exists")
        print("   - Check username/password in script")
        sys.exit(1)
    
    # Step 2: Read CSV file
    print("\n2️⃣ Reading CSV file...")
    drugs_data = read_csv_file(csv_file)
    
    if not drugs_data:
        print("💡 CSV Troubleshooting:")
        print("   - Check file exists and readable")
        print("   - Ensure format: nama_obat;nama_internasional")
        print("   - Try different encoding (UTF-8, CP1252)")
        sys.exit(1)
    
    # Step 3: Import to database
    print("\n3️⃣ Importing to database...")
    success = import_drugs_to_database(drugs_data)
    
    if success:
        print(f"\n🎉 Import completed successfully!")
        print(f"\n🧪 Test URLs:")
        print(f"   - Drug stats: http://localhost:8000/api/drugs/stats")
        print(f"   - Search test: http://localhost:8000/api/drugs/search?q=para")
        print(f"\n🔄 Next steps:")
        print(f"   1. Restart backend server")
        print(f"   2. Test drug search di frontend")
        print(f"   3. Complete MedicationInput component")
    else:
        print(f"\n💥 Import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()