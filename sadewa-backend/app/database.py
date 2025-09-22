"""
Database configuration and utility functions.
Enhanced version with migration support and monitoring functions.
"""

import os
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from sqlalchemy.pool import QueuePool
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

try:
    from app.models import Base
except ImportError:
    logger.warning("Could not import 'Base' from 'app.models'. Using a placeholder. This is fine for setup, but might cause issues with table creation if models aren't defined.")
    Base = declarative_base()


def get_database_url():
    """Get database URL from various environment variables."""
    db_url_vars = ['DATABASE_URL', 'MYSQL_URL', 'DB_URL', 'RAILWAY_MYSQL_URL']
    for var in db_url_vars:
        url = os.getenv(var)
        if url:
            if url.startswith('mysql://'):
                url = url.replace('mysql://', 'mysql+pymysql://')
            logger.info(f"✅ Using database URL from {var}")
            return url

    # Fallback to build URL from components
    logger.info("🔧 Building database URL from component environment variables.")
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '3306')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    database = os.getenv('DB_NAME', 'sadewa_db')
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

# Initialize engine and SessionLocal as None
engine = None
SessionLocal = None

try:
    DATABASE_URL = get_database_url()
    if not DATABASE_URL:
        raise ConnectionError("Database URL not found in environment variables.")

    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Test connection on startup
    with engine.connect() as connection:
        logger.info("✅ Database connection successful.")

except (ConnectionError, SQLAlchemyError) as e:
    logger.error(f"❌ Database initialization failed: {e}")


# --- FUNGSI YANG DIBUTUHKAN OLEH main.py ---

def test_database_connection():
    """
    Tests the database connection by executing a simple query.
    Returns True if successful, False otherwise.
    """
    if not engine:
        return False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def get_database_stats():
    """
    Retrieves statistics from the database like version and connection count.
    """
    if not engine:
        raise ConnectionError("Database engine is not initialized.")
    try:
        with engine.connect() as connection:
            version_result = connection.execute(text("SELECT VERSION()")).scalar()
            threads_connected_result = connection.execute(text("SHOW STATUS LIKE 'Threads_connected'")).fetchone()
            stats = {
                "db_version": version_result,
                "threads_connected": int(threads_connected_result[1]) if threads_connected_result else 0
            }
            return stats
    except SQLAlchemyError as e:
        logger.error(f"Could not retrieve database stats: {e}")
        raise

# --- FUNGSI LAINNYA ---

def get_db():
    """Database session dependency for FastAPI."""
    if not SessionLocal:
        raise RuntimeError("Database not available - check configuration")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables defined in Base.metadata."""
    if not engine:
        logger.error("❌ Cannot create tables - no database engine.")
        return False
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False

def check_tables_exist():
    """Check if required tables exist in the database."""
    if not engine:
        return False
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        # You can define required_tables here if needed
        # required_tables = ['patients', 'medical_records']
        # missing = set(required_tables) - set(existing_tables)
        logger.info(f"✅ Found tables: {existing_tables}")
        return True
    except Exception as e:
        logger.error(f"❌ Error checking tables: {e}")
        return False

