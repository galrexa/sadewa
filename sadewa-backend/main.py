"""
SADEWA Backend Main Application - DAY 2
Enhanced dengan semua routers dan middleware
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import patients, icd10, interactions, drugs  # Tambah drugs

import os

# Import routers
from app.routers import patients, icd10, interactions

# Import database (untuk health check)
from app.database import engine
from sqlalchemy import text

app = FastAPI(
    title="SADEWA - Smart Assistant for Drug & Evidence Warning",
    description="Enhanced AI-powered drug interaction analysis system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware untuk frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: ganti dengan domain spesifik
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers dengan prefix
app.include_router(patients.router, prefix="/api", tags=["patients"])
app.include_router(icd10.router, prefix="/api/icd10", tags=["icd10"])
app.include_router(interactions.router, prefix="/api", tags=["interactions"])
app.include_router(patients.router, prefix="/api", tags=["patients"])
app.include_router(icd10.router, prefix="/api/icd10", tags=["icd10"])
app.include_router(interactions.router, prefix="/api", tags=["interactions"])
app.include_router(drugs.router, prefix="/api", tags=["drugs"])  # Tambah ini

@app.get("/")
async def root():
    """Root endpoint dengan informasi API"""
    return {
        "message": "SADEWA API - Smart Assistant for Drug & Evidence Warning",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Enhanced health check dengan database status"""
    try:
        # Test database connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            db_status = "connected"
            
            # Count ICD-10 records
            icd_result = connection.execute(text("SELECT COUNT(*) FROM icds"))
            icd_count = icd_result.scalar()
            
            # Count drugs records (jika table sudah ada)
            try:
                drug_result = connection.execute(text("SELECT COUNT(*) FROM drugs WHERE is_active = TRUE"))
                drug_count = drug_result.scalar()
            except:
                drug_count = 0
    
    except Exception as e:
        db_status = f"error: {str(e)}"
        icd_count = 0
        drug_count = 0
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "database": {
            "status": db_status,
            "icd10_records": icd_count,
            "drug_records": drug_count  # Tambah ini
        },
        "services": {
            "groq": "available",
            "mysql": db_status
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "detail": "Endpoint not found",
        "available_endpoints": {
            "health": "/health",
            "patients": "/api/patients",
            "icd10_search": "/api/icd10/search",
            "drug_interactions": "/api/analyze-interactions",
            "groq_test": "/api/test-groq",
            "docs": "/docs"
        }
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "detail": "Internal server error",
        "message": "Please check server logs for details",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)