# fix_monitoring.py
"""
Fix untuk monitoring endpoint yang missing performance_metrics
Tambahkan baris ini ke main.py Anda
"""

from fastapi import FastAPI
from datetime import datetime
import time

# Tambahkan endpoint ini ke main.py Anda jika belum ada

@app.get("/monitoring")
async def monitoring_dashboard():
    """System monitoring endpoint for ops dashboard - FIXED VERSION"""
    try:
        uptime = datetime.now() - app.state.start_time
        
        # Performance metrics - FIXED
        performance_metrics = {
            "uptime_hours": round(uptime.total_seconds() / 3600, 2),
            "total_requests": app.state.request_count,
            "requests_per_hour": round(
                app.state.request_count / max(uptime.total_seconds() / 3600, 0.001), 2
            ),
            "avg_response_time_ms": round(
                app.state.total_processing_time / max(app.state.request_count, 1), 2
            )
        }
        
        # Database connection pool stats - with error handling
        pool_stats = {}
        try:
            if hasattr(engine, 'pool'):
                pool_stats = {
                    "pool_size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow(),
                    "invalid": engine.pool.invalid()
                }
        except Exception as e:
            pool_stats = {"error": f"Could not get pool stats: {str(e)}"}
        
        # Recent database activity
        database_activity = {"status": "checking..."}
        try:
            with engine.connect() as connection:
                # Get recent activity (last hour)
                activity_query = text("""
                    SELECT 
                        COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as new_patients_1h,
                        COUNT(*) as total_patients
                    FROM patients
                """)
                
                activity_stats = connection.execute(activity_query).fetchone()
                
                database_activity = {
                    "new_patients_last_hour": activity_stats.new_patients_1h if activity_stats else 0,
                    "total_patients": activity_stats.total_patients if activity_stats else 0,
                    "last_checked": datetime.now().isoformat()
                }
        except Exception as e:
            database_activity = {"error": f"Could not retrieve activity: {str(e)}"}
        
        return {
            "system_info": {
                "version": "2.1.0-optimized",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "start_time": app.state.start_time.isoformat(),
                "current_time": datetime.now().isoformat()
            },
            "performance_metrics": performance_metrics,  # FIXED - ini yang missing
            "database": {
                "connection_pool": pool_stats,
                "activity": database_activity
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Monitoring endpoint failed: {e}")
        return {
            "error": "Monitoring data partially unavailable",
            "details": str(e),
            "timestamp": datetime.now().isoformat(),
            "basic_info": {
                "version": "2.1.0-optimized",
                "status": "running_with_errors"
            }
        }

# Juga pastikan app.state initialization ada di startup
@app.on_event("startup")
async def startup_event():
    """Initialize app state"""
    app.state.request_count = 0
    app.state.total_processing_time = 0.0
    app.state.start_time = datetime.now()
    
    print("✅ App state initialized")
    print(f"🕒 Start time: {app.state.start_time}")