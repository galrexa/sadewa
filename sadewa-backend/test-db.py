# test_db_connection.py
from app.database import engine
from sqlalchemy import text

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            print("✅ Database connection successful!")
            print(f"   Test query result: {result.fetchone()}")
            
            # Test ICD-10 table exists
            result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Found tables: {tables}")
            
            # Test ICD-10 data
            if any('icd' in table.lower() for table in tables):
                icd_table = next(table for table in tables if 'icd' in table.lower())
                result = connection.execute(text(f"SELECT COUNT(*) FROM {icd_table}"))
                count = result.fetchone()[0]
                print(f"✅ ICD-10 records: {count}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Pastikan MySQL server running dan database 'sadewa_db' sudah dibuat")

if __name__ == "__main__":
    test_connection()