# sadewa-backend/check_icds_structure.py
from app.database import engine
from sqlalchemy import text

def check_icds_structure():
    try:
        with engine.connect() as connection:
            # Cek struktur table icds
            result = connection.execute(text("DESCRIBE icds"))
            columns = result.fetchall()
            
            print("=== STRUKTUR TABLE ICDS ===")
            for col in columns:
                print(f"{col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]} | {col[5]}")
            
            # Cek sample data
            result = connection.execute(text("SELECT * FROM icds LIMIT 3"))
            rows = result.fetchall()
            
            print("\n=== SAMPLE DATA ===")
            for row in rows:
                print(row)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_icds_structure()