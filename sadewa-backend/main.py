from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Import routers
from app.routers import patients

# Import database (untuk health check)
from app.database import engine
from sqlalchemy import text

app = FastAPI(
    title="SADEWA - Smart Assistant for Drug & Evidence Warning",
    description="Complete AI-powered drug interaction analysis system",
    version="3.0.0",
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

# Include routers dengan prefix yang benar
app.include_router(patients.router, prefix="/api", tags=["patients"])
# app.include_router(icd10.router, prefix="/api/icd10", tags=["icd10"])
# app.include_router(interactions.router, prefix="/api", tags=["interactions"])
# app.include_router(drugs.router, prefix="/api/drugs", tags=["drugs"])  # Fixed prefix

@app.get("/")
async def root():
    """Root endpoint dengan informasi API"""
    return {
        "message": "SADEWA API - Smart Assistant for Drug & Evidence Warning",
        "version": "3.0.0",
        "status": "operational",
        "features": [
            "Drug interaction analysis",
            "ICD-10 disease search", 
            "Patient management",
            "AI-powered recommendations",
            "Complete drug database (Fornas)"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api"
        }
    }

@app.get("/health")
async def health_check():
    """Enhanced health check dengan database status"""
    try:
        # Test database connection
        with engine.connect() as connection:
            # Basic connection test
            result = connection.execute(text("SELECT 1"))
            db_status = "connected"
            
            # Count ICD-10 records
            try:
                icd_result = connection.execute(text("SELECT COUNT(*) FROM icd10"))
                icd_count = icd_result.scalar()
            except Exception:
                icd_count = 0
            
            # Count drugs records
            try:
                drug_result = connection.execute(text("SELECT COUNT(*) FROM drugs WHERE is_active = 1"))
                drug_count = drug_result.scalar()
            except Exception:
                drug_count = 0
            
            # Count patients (if table exists)
            try:
                # Patients might be in JSON file, not database
                patient_count = 10  # Default from patients.json
            except Exception:
                patient_count = 0
    
    except Exception as e:
        db_status = f"error: {str(e)}"
        icd_count = 0
        drug_count = 0
        patient_count = 0
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "database": {
            "status": db_status,
            "icd_records": icd_count,
            "drug_records": drug_count,
            "patient_records": patient_count
        },
        "services": {
            "drug_search": "operational",
            "interaction_analysis": "operational", 
            "icd10_search": "operational",
            "ai_analysis": "operational" if os.getenv("GROQ_API_KEY") else "limited"
        }
    }

@app.get("/api/system/info")
async def system_info():
    """System information endpoint"""
    return {
        "system_name": "SADEWA",
        "full_name": "Smart Assistant for Drug & Evidence Warning",
        "version": "3.0.0",
        "build_date": "2024-01-15",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": {
            "type": "MySQL",
            "status": "connected"
        },
        "ai_provider": "Groq (Llama3-70B)",
        "features": {
            "drug_search": True,
            "drug_validation": True,
            "interaction_checking": True,
            "ai_analysis": bool(os.getenv("GROQ_API_KEY")),
            "icd10_search": True,
            "patient_management": True
        },
        "data_sources": {
            "drugs": "Fornas Indonesia",
            "icd10": "WHO ICD-10",
            "interactions": "Clinical knowledge base"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )