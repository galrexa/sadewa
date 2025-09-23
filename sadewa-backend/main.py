import time
import logging
import os
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import uvicorn

# Import optimized routers and database components
from app.database import engine, get_database_stats, test_database_connection
from app.routers.patients import router as patients_router
from app.routers.medical_records import router as medical_records_router
from app.routers.ai_diagnosis import router as ai_diagnosis_router
# from app.routers.interactions import router as interactions_router

# Import existing routers
from app.routers import drugs, icd10, interactions

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app with optimized settings
app = FastAPI(
    title="SADEWA - Smart Assistant for Drug & Evidence Warning",
    description="""
    ## Complete AI-powered Medical Information System

    ### Key Features:
    - **Patient Registration & Management** - Optimized CRUD operations
    - **Medical Records (Anamnesis)** - Structured symptom tracking
    - **AI Diagnosis Analysis** - Intelligent diagnostic suggestions
    - **Drug Interaction Analysis** - Real-time safety checking
    - **Performance Monitoring** - Built-in analytics and caching
    """,
    version="2.1.0-optimized",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== MIDDLEWARE CONFIGURATION =====

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive for development, tighten for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Processing-Time"]
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global state for monitoring
app.state.request_count = 0
app.state.total_processing_time = 0.0
app.state.start_time = datetime.now()

# ===== CUSTOM MIDDLEWARE =====

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Performance monitoring and request logging middleware"""
    start_time = time.perf_counter()
    request_id = f"{int(time.time())}-{os.urandom(4).hex()}"
    request.state.request_id = request_id

    try:
        response = await call_next(request)
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Update global stats
        app.state.request_count += 1
        app.state.total_processing_time += processing_time
        
        # Add performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"

        # Log slow requests
        if processing_time > 1000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {processing_time:.2f}ms (Request ID: {request_id})"
            )
        
        return response
        
    except Exception as e:
        processing_time = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"after {processing_time:.2f}ms - Error: {e} (Request ID: {request_id})",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        )

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


# ===== EXCEPTION HANDLERS =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": getattr(request.state, 'request_id', 'unknown'),
        }
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Database error handler"""
    logger.error(f"Database error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=503, # Service Unavailable
        content={
            "error": "Database service is temporarily unavailable.",
            "request_id": getattr(request.state, 'request_id', 'unknown'),
        }
    )

# ===== ROUTER INCLUSION =====

app.include_router(patients_router, prefix="/api", tags=["Patients"])
app.include_router(medical_records_router, prefix="/api", tags=["Medical Records"])
app.include_router(ai_diagnosis_router, prefix="/api", tags=["AI Diagnosis"])
app.include_router(icd10.router, prefix="/api/icd10", tags=["ICD10"])
app.include_router(interactions.router, prefix="/api", tags=["Interactions"])
app.include_router(drugs.router, prefix="/api/drugs", tags=["Drugs"])

# ===== ROOT & HEALTH ENDPOINTS =====

@app.get("/", tags=["System"])
async def root():
    """Root endpoint with system information."""
    uptime = datetime.now() - app.state.start_time
    avg_processing_time = (
        app.state.total_processing_time / app.state.request_count
        if app.state.request_count > 0 else 0
    )
    return {
        "message": "SADEWA API - Smart Assistant for Drug & Evidence Warning",
        "version": app.version,
        "status": "operational",
        "performance": {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": app.state.request_count,
            "avg_processing_time_ms": round(avg_processing_time, 2)
        },
        "docs": app.docs_url,
    }

@app.get("/health", tags=["System"])
async def health_check():
    """Comprehensive health check endpoint."""
    start_time = time.perf_counter()
    
    # Check Database
    db_ok = test_database_connection()
    
    total_time = (time.perf_counter() - start_time) * 1000
    
    status_code = 200 if db_ok else 503
    
    response_content = {
        "status": "healthy" if db_ok else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "version": app.version,
        "checks": {
            "database": {
                "status": "healthy" if db_ok else "unhealthy"
            }
        },
        "total_check_time_ms": round(total_time, 2)
    }
    
    return JSONResponse(status_code=status_code, content=response_content)

# ===== STARTUP & SHUTDOWN EVENTS =====

@app.on_event("startup")
def startup_event():
    """Application startup initialization."""
    logger.info(f"🚀 Starting SADEWA API v{app.version}")
    if test_database_connection():
        logger.info("✅ Database connection established.")
        try:
            stats = get_database_stats()
            logger.info(f"📊 Database stats: {stats}")
        except Exception as e:
            logger.warning(f"Could not get initial database stats: {e}")
    else:
        logger.error("❌ Database connection failed. Please check database configuration and connectivity.")

@app.on_event("shutdown")
def shutdown_event():
    """Application shutdown cleanup."""
    logger.info("🛑 Shutting down SADEWA API")
    if engine:
        engine.dispose()
        logger.info("🔌 Database connection pool closed.")
    logger.info("✅ SADEWA API shutdown completed.")

# ===== DEVELOPMENT SERVER =====

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=is_development,
        log_level="info"
    )
