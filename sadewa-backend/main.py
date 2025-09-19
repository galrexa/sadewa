"""
Main application file for the SADEWA API.

This file initializes the FastAPI application, sets up middleware,
includes API routers, and defines root and health check endpoints.
"""

import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
from app.routers import drugs, icd10, interactions, patients

app = FastAPI(
    title="SADEWA - Smart Assistant for Drug & Evidence Warning",
    description="Complete AI-powered drug interaction analysis system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with correct prefixes
app.include_router(patients.router, prefix="/api", tags=["patients"])
app.include_router(icd10.router, prefix="/api/icd10", tags=["icd10"])
app.include_router(interactions.router, prefix="/api", tags=["interactions"])
app.include_router(drugs.router, prefix="/api/drugs", tags=["drugs"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "SADEWA API - Smart Assistant for Drug & Evidence Warning",
        "version": "1.0.0",
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
    """Enhanced health check with database status."""
    db_status = "error"
    icd_count = 0
    drug_count = 0
    patient_count = 0  # Default from patients.json

    try:
        with engine.connect() as connection:
            # Basic connection test (result variable is not needed)
            connection.execute(text("SELECT 1"))
            db_status = "connected"

            # Count ICD-10 records
            try:
                icd_result = connection.execute(text("SELECT COUNT(*) FROM icd10"))
                icd_count = icd_result.scalar()
            except SQLAlchemyError:
                icd_count = 0  # Keep it at 0 if this specific query fails

            # Count drugs records
            try:
                drug_result = connection.execute(
                    text("SELECT COUNT(*) FROM drugs WHERE is_active = 1")
                )
                drug_count = drug_result.scalar()
            except SQLAlchemyError:
                drug_count = 0  # Keep it at 0 if this specific query fails

            # Patient count is hardcoded as it comes from a JSON file
            patient_count = 10

    except SQLAlchemyError as e:
        db_status = f"error: {str(e)}"
        # All counts remain 0 if the initial connection fails

    ai_status = "operational" if os.getenv("GROQ_API_KEY") else "limited"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
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
            "ai_analysis": ai_status
        }
    }


@app.get("/api/system/info")
async def system_info():
    """System information endpoint."""
    return {
        "system_name": "SADEWA",
        "full_name": "Smart Assistant for Drug & Evidence Warning",
        "version": "1.0.0",
        "build_date": "2025-09-01",
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
