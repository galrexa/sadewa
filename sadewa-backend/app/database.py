# app/database.py
"""
Database configuration and connection setup
"""

import os
from sqlalchemy import create_engine, text  # ✅ TAMBAH import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    db_url_vars = [
        'DATABASE_URL',
        'MYSQL_URL', 
        'DB_URL',
        'RAILWAY_MYSQL_URL'
    ]
    
    for var in db_url_vars:
        url = os.getenv(var)
        if url:
            # Clean URL - remove prefix if exists
            if '=' in url and url.startswith(var):
                url = url.split('=', 1)[1]
            
            # Ensure mysql+pymysql driver
            if url.startswith('mysql://'):
                url = url.replace('mysql://', 'mysql+pymysql://')
            
            print(f"✅ Using database URL from {var}")
            return url
    
    # Fallback: build URL from components
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '3306')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    database = os.getenv('DB_NAME', 'sadewa_db')
    
    if password:
        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    else:
        url = f"mysql+pymysql://{user}@{host}:{port}/{database}"
    
    print(f"🔧 Built database URL from components")
    return url

# Database setup
try:
    DATABASE_URL = get_database_url()
    if not DATABASE_URL:
        raise Exception("No database configuration found!")
    
    # Create engine dengan MySQL-specific settings
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set True untuk debug SQL queries
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=30,
        connect_args={
            "charset": "utf8mb4",
            "autocommit": False
        }
    )
    
    # Test connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✅ Database connection test successful")
        
        # Test patients table exists
        result = connection.execute(text("SHOW TABLES LIKE 'patients'"))
        if result.fetchone():
            print("✅ Patients table found")
        else:
            print("⚠️  Patients table not found!")
    
    print("✅ Database engine initialized successfully")
    
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    print("🔄 Creating minimal engine for development...")
    
    # Fallback engine (untuk development tanpa database)
    engine = None

# SQLAlchemy setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

def get_db():
    """Database session dependency for FastAPI"""
    if not engine:
        raise Exception("Database not available")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()