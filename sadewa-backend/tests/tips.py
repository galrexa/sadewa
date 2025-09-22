# performance_tips.py
"""
Performance optimization tips for SADEWA API
"""

# 1. DATABASE CONNECTION OPTIMIZATION
# Tambahkan ini ke database.py Anda:

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Optimized engine configuration
engine = create_engine(
    DATABASE_URL,
    
    # Connection Pool Optimization
    poolclass=QueuePool,
    pool_size=10,              # Increased from 5
    max_overflow=20,           # Increased from 10  
    pool_timeout=20,           # Reduced from 30
    pool_recycle=1800,         # 30 minutes instead of 1 hour
    pool_pre_ping=True,
    
    # Connection optimization
    connect_args={
        "charset": "utf8mb4",
        "autocommit": False,
        "connect_timeout": 5,   # Reduced from 10
        
        # MySQL performance settings
        "sql_mode": "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO",
        "isolation_level": "READ_COMMITTED",
        
        # Additional MySQL optimizations
        "use_unicode": True,
        "init_command": """
            SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';
            SET SESSION transaction_isolation = 'READ-COMMITTED';
            SET SESSION wait_timeout = 300;
            SET SESSION interactive_timeout = 300;
            SET SESSION innodb_lock_wait_timeout = 10;
        """
    },
    echo=False  # Disable SQL logging in production
)

# 2. BACKGROUND TASK OPTIMIZATION
# Untuk patient registration, pindahkan heavy operations ke background:

import asyncio
from fastapi import BackgroundTasks

async def optimized_patient_registration(patient_data, background_tasks):
    """Optimized patient registration with minimal blocking operations"""
    
    # 1. Quick database insert (main thread)
    start_time = time.time()
    
    # Simple insert without complex operations
    insert_query = text("""
        INSERT INTO patients (name, age, gender, phone, weight_kg, created_at, updated_at)
        VALUES (:name, :age, :gender, :phone, :weight_kg, NOW(), NOW())
    """)
    
    result = db.execute(insert_query, {
        "name": patient_data.name,
        "age": patient_data.age,
        "gender": patient_data.gender,
        "phone": patient_data.phone,
        "weight_kg": patient_data.weight_kg
    })
    
    new_patient_id = result.lastrowid
    db.commit()
    
    # 2. Background operations (non-blocking)
    background_tasks.add_task(
        process_patient_background_data,
        new_patient_id,
        patient_data.medical_history,
        patient_data.allergies,
        patient_data.risk_factors
    )
    
    # 3. Quick response
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "id": new_patient_id,
        "name": patient_data.name,
        "age": patient_data.age,
        "gender": patient_data.gender,
        "phone": patient_data.phone,
        "weight_kg": patient_data.weight_kg,
        "patient_code": f"P{new_patient_id:04d}",
        "processing_time_ms": processing_time,
        "background_processing": "in_progress"
    }

async def process_patient_background_data(patient_id, medical_history, allergies, risk_factors):
    """Process heavy operations in background"""
    try:
        # Add allergies
        if allergies:
            for allergen in allergies:
                # Insert allergies
                pass
        
        # Update medical history
        if medical_history or risk_factors:
            # Update profile data
            pass
        
        # Create timeline entry
        # Timeline operations
        pass
        
    except Exception as e:
        logger.error(f"Background processing failed for patient {patient_id}: {e}")

# 3. CACHING OPTIMIZATION
# Add simple in-memory caching for frequent queries:

from functools import lru_cache
import time

# Cache for patient statistics (5 minute cache)
_stats_cache = {"data": None, "timestamp": 0}
CACHE_DURATION = 300  # 5 minutes

async def get_cached_patient_stats():
    """Get patient statistics with caching"""
    current_time = time.time()
    
    # Check cache
    if (_stats_cache["data"] and 
        current_time - _stats_cache["timestamp"] < CACHE_DURATION):
        return _stats_cache["data"]
    
    # Fetch new data
    stats = await get_patient_statistics_from_db()
    
    # Update cache
    _stats_cache["data"] = stats
    _stats_cache["timestamp"] = current_time
    
    return stats

# 4. QUERY OPTIMIZATION
# Use more efficient queries:

async def optimized_patient_search(query_params):
    """Optimized patient search with better queries"""
    
    # Use LIMIT early in query
    # Use proper indexes
    # Avoid SELECT *
    
    search_query = text("""
        SELECT id, name, age, gender, phone, created_at, updated_at
        FROM patients 
        WHERE name LIKE :pattern 
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    # Avoid heavy computations in Python
    # Let database do the work
    
# 5. MIDDLEWARE OPTIMIZATION
# Optimize request processing middleware:

@app.middleware("http")
async def optimized_performance_middleware(request, call_next):
    """Lightweight performance middleware"""
    
    start_time = time.time()
    
    # Skip heavy logging for health checks
    if request.url.path in ["/health", "/", "/docs"]:
        response = await call_next(request)
        response.headers["X-Processing-Time"] = f"{(time.time() - start_time) * 1000:.1f}ms"
        return response
    
    # Normal processing for other endpoints
    response = await call_next(request)
    
    # Light statistics update
    processing_time = (time.time() - start_time) * 1000
    response.headers["X-Processing-Time"] = f"{processing_time:.1f}ms"
    
    # Update global stats (lightweight)
    app.state.request_count += 1
    app.state.total_processing_time += processing_time
    
    return response

# 6. QUICK PERFORMANCE TEST
async def run_performance_test():
    """Quick performance test"""
    
    print("🚀 Running Performance Test...")
    
    # Test database connection speed
    start = time.time()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    db_time = (time.time() - start) * 1000
    
    print(f"🗄️  Database connection: {db_time:.1f}ms")
    
    # Test simple query speed
    start = time.time()
    with engine.connect() as conn:
        conn.execute(text("SELECT COUNT(*) FROM patients"))
    query_time = (time.time() - start) * 1000
    
    print(f"📊 Simple query: {query_time:.1f}ms")
    
    # Performance recommendations
    if db_time > 50:
        print("⚠️  Database connection slow - check network/config")
    if query_time > 100:
        print("⚠️  Query performance slow - check indexes")
    
    print("✅ Performance test completed")

if __name__ == "__main__":
    # Run performance test
    import asyncio
    asyncio.run(run_performance_test())