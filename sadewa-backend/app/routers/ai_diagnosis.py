# app/routers/ai_diagnosis_optimized.py
"""
OPTIMIZED AI Diagnosis & Drug Interaction API for SADEWA
Priority: AI Analysis + Drug Interactions + Performance Caching
"""

import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.database import get_db
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== ENUMS =====

class InteractionSeverity(str, Enum):
    MAJOR = "MAJOR"
    MODERATE = "MODERATE"
    MINOR = "MINOR"

class AIAnalysisType(str, Enum):
    DIAGNOSIS = "diagnosis"
    DRUG_INTERACTION = "drug_interaction"
    RISK_ASSESSMENT = "risk_assessment"
    TREATMENT_RECOMMENDATION = "treatment_recommendation"

# ===== PYDANTIC SCHEMAS =====

class DrugInteractionRequest(BaseModel):
    """Schema untuk analisis drug interaction"""
    medications: List[str] = Field(..., min_items=1, description="Daftar obat yang akan dianalisis")
    patient_id: Optional[int] = Field(None, description="ID pasien (optional)")
    include_cache: bool = Field(True, description="Gunakan cache jika tersedia")
    
    @validator('medications')
    def validate_medications(cls, v):
        # Remove duplicates and empty strings
        cleaned = list(set([med.strip() for med in v if med.strip()]))
        if len(cleaned) < 1:
            raise ValueError('Minimal 1 obat harus diisi')
        return cleaned

class DrugInteractionResult(BaseModel):
    """Schema hasil drug interaction"""
    drug_1: str
    drug_2: str
    severity: InteractionSeverity
    description: str
    mechanism: Optional[str] = None
    clinical_effect: Optional[str] = None
    recommendation: Optional[str] = None
    evidence_level: Optional[str] = None

class DrugInteractionResponse(BaseModel):
    """Schema response drug interaction analysis"""
    input_medications: List[str]
    total_interactions: int
    high_risk_interactions: int
    interactions: List[DrugInteractionResult]
    patient_allergies: List[str] = []
    contraindications: List[str] = []
    processing_time_ms: float
    cache_used: bool = False
    ai_analysis: Optional[Dict[str, Any]] = None

class AIAnalysisRequest(BaseModel):
    """Schema untuk AI analysis request"""
    patient_id: int = Field(..., description="ID pasien")
    analysis_type: AIAnalysisType = Field(..., description="Jenis analisis AI")
    
    # Symptoms data
    symptoms: Optional[List[str]] = Field(default=[], description="Daftar gejala")
    chief_complaint: Optional[str] = Field(None, description="Keluhan utama")
    vital_signs: Optional[Dict[str, Any]] = Field(None, description="Tanda vital")
    
    # Medical history
    medical_history: Optional[List[str]] = Field(default=[], description="Riwayat penyakit")
    current_medications: Optional[List[str]] = Field(default=[], description="Obat saat ini")
    allergies: Optional[List[str]] = Field(default=[], description="Riwayat alergi")
    
    # Additional context
    age: Optional[int] = Field(None, description="Umur pasien")
    gender: Optional[str] = Field(None, description="Jenis kelamin")
    weight_kg: Optional[float] = Field(None, description="Berat badan")

class AIAnalysisResponse(BaseModel):
    """Schema response AI analysis"""
    patient_id: int
    analysis_type: str
    confidence_score: float
    
    # Diagnosis results
    suggested_diagnoses: List[Dict[str, Any]] = []
    differential_diagnoses: List[str] = []
    
    # Drug interaction results
    drug_interactions: Optional[DrugInteractionResponse] = None
    
    # Treatment recommendations
    treatment_recommendations: List[str] = []
    monitoring_recommendations: List[str] = []
    
    # Risk assessment
    risk_level: str = "low"  # low, medium, high, critical
    risk_factors: List[str] = []
    
    # AI metadata
    ai_model_version: str
    processing_time_ms: float
    created_at: datetime

# ===== UTILITY FUNCTIONS =====

def generate_drug_combination_hash(medications: List[str]) -> str:
    """Generate hash untuk drug combination caching"""
    sorted_meds = sorted([med.lower().strip() for med in medications])
    combined = "|".join(sorted_meds)
    return hashlib.md5(combined.encode()).hexdigest()

async def get_cached_interaction_result(
    drug_hash: str,
    db: Session
) -> Optional[Dict[str, Any]]:
    """Get cached drug interaction result"""
    try:
        cache_query = text("""
            SELECT interaction_result, severity_max, last_checked
            FROM drug_interaction_cache
            WHERE drug_combination_hash = :hash
            AND expiry_date > NOW()
            LIMIT 1
        """)
        
        cached = db.execute(cache_query, {"hash": drug_hash}).fetchone()
        
        if cached:
            return {
                "result": json.loads(cached.interaction_result),
                "severity_max": cached.severity_max,
                "last_checked": cached.last_checked
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting cached result: {e}")
        return None

async def save_interaction_cache(
    drug_hash: str,
    medications: List[str],
    interaction_result: Dict[str, Any],
    severity_max: str,
    db: Session
):
    """Save interaction result to cache"""
    try:
        # Set cache expiry (7 days)
        expiry_date = datetime.now() + timedelta(days=7)
        
        cache_query = text("""
            INSERT INTO drug_interaction_cache 
            (drug_combination_hash, drug_names, interaction_result, severity_max, expiry_date)
            VALUES (:hash, :drugs, :result, :severity, :expiry)
            ON DUPLICATE KEY UPDATE 
                interaction_result = :result,
                severity_max = :severity,
                last_checked = NOW(),
                expiry_date = :expiry
        """)
        
        db.execute(cache_query, {
            "hash": drug_hash,
            "drugs": json.dumps(medications),
            "result": json.dumps(interaction_result),
            "severity": severity_max,
            "expiry": expiry_date
        })
        db.commit()
        
    except Exception as e:
        logger.error(f"Error saving cache: {e}")
        db.rollback()

async def analyze_drug_interactions_db(
    medications: List[str],
    db: Session
) -> List[DrugInteractionResult]:
    """Analyze drug interactions using database"""
    interactions = []
    
    try:
        # Check both directions of interaction
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                drug_1 = medications[i].strip()
                drug_2 = medications[j].strip()
                
                # Search in both simple and complex interaction tables
                interaction_query = text("""
                    SELECT 
                        drug_a as drug_1, drug_b as drug_2, severity, description, recommendation,
                        NULL as mechanism, NULL as clinical_effect, NULL as evidence_level
                    FROM simple_drug_interactions 
                    WHERE ((LOWER(drug_a) LIKE :drug1 OR LOWER(drug_a) LIKE :drug1_partial) 
                           AND (LOWER(drug_b) LIKE :drug2 OR LOWER(drug_b) LIKE :drug2_partial))
                       OR ((LOWER(drug_a) LIKE :drug2 OR LOWER(drug_a) LIKE :drug2_partial)
                           AND (LOWER(drug_b) LIKE :drug1 OR LOWER(drug_b) LIKE :drug1_partial))
                    AND is_active = 1
                    
                    UNION
                    
                    SELECT 
                        drug_1, drug_2, severity, description, recommendation,
                        mechanism, clinical_effect, evidence_level
                    FROM drug_interactions 
                    WHERE ((LOWER(drug_1) LIKE :drug1 OR LOWER(drug_1) LIKE :drug1_partial)
                           AND (LOWER(drug_2) LIKE :drug2 OR LOWER(drug_2) LIKE :drug2_partial))
                       OR ((LOWER(drug_1) LIKE :drug2 OR LOWER(drug_1) LIKE :drug2_partial)
                           AND (LOWER(drug_2) LIKE :drug1 OR LOWER(drug_2) LIKE :drug1_partial))
                    AND is_active = 1
                """)
                
                drug1_pattern = f"%{drug_1.lower()}%"
                drug2_pattern = f"%{drug_2.lower()}%"
                drug1_partial = f"%{drug_1.lower()[:5]}%" if len(drug_1) > 5 else drug1_pattern
                drug2_partial = f"%{drug_2.lower()[:5]}%" if len(drug_2) > 5 else drug2_pattern
                
                results = db.execute(interaction_query, {
                    "drug1": drug1_pattern,
                    "drug2": drug2_pattern,
                    "drug1_partial": drug1_partial,
                    "drug2_partial": drug2_partial
                }).fetchall()
                
                for result in results:
                    interactions.append(DrugInteractionResult(
                        drug_1=result.drug_1,
                        drug_2=result.drug_2,
                        severity=InteractionSeverity(result.severity),
                        description=result.description or "Interaksi obat terdeteksi",
                        mechanism=result.mechanism,
                        clinical_effect=result.clinical_effect,
                        recommendation=result.recommendation,
                        evidence_level=result.evidence_level
                    ))
        
        return interactions
        
    except Exception as e:
        logger.error(f"Error analyzing drug interactions: {e}")
        return []

async def get_patient_allergies(patient_id: int, db: Session) -> List[str]:
    """Get patient allergies"""
    try:
        allergy_query = text("""
            SELECT allergen FROM patient_allergies 
            WHERE patient_id = :patient_id
        """)
        
        allergies = db.execute(allergy_query, {"patient_id": patient_id}).fetchall()
        return [allergy.allergen for allergy in allergies]
        
    except Exception as e:
        logger.error(f"Error getting patient allergies: {e}")
        return []

async def check_contraindications(
    medications: List[str],
    patient_allergies: List[str],
    medical_history: List[str]
) -> List[str]:
    """Check for contraindications"""
    contraindications = []
    
    # Check allergy contraindications
    for med in medications:
        for allergy in patient_allergies:
            if allergy.lower() in med.lower() or med.lower() in allergy.lower():
                contraindications.append(f"ALERGI: {med} - pasien alergi terhadap {allergy}")
    
    # Add more contraindication logic here based on medical history
    # This would be expanded with more comprehensive rules
    
    return contraindications

async def call_ai_analysis(
    analysis_request: Dict[str, Any],
    analysis_type: str
) -> Dict[str, Any]:
    """Call AI service (Groq) for analysis"""
    try:
        # This would be the actual AI service call
        # For now, return mock response
        
        if analysis_type == "drug_interaction":
            return {
                "ai_recommendations": [
                    "Monitor patient closely for drug interactions",
                    "Consider alternative medications if severe interactions found",
                    "Adjust dosing based on patient weight and age"
                ],
                "confidence": 0.85,
                "model_version": "llama3-70b-8192"
            }
        elif analysis_type == "diagnosis":
            return {
                "suggested_diagnoses": [
                    {"diagnosis": "Common cold", "confidence": 0.7, "icd_code": "J00"},
                    {"diagnosis": "Viral upper respiratory infection", "confidence": 0.6, "icd_code": "J06.9"}
                ],
                "confidence": 0.75,
                "model_version": "llama3-70b-8192"
            }
        
        return {"confidence": 0.5, "model_version": "llama3-70b-8192"}
        
    except Exception as e:
        logger.error(f"AI service call failed: {e}")
        return {"error": str(e), "confidence": 0.0, "model_version": "error"}

async def save_ai_analysis_log(
    patient_id: int,
    medical_record_id: Optional[int],
    analysis_type: str,
    input_data: Dict[str, Any],
    ai_response: Dict[str, Any],
    confidence_score: float,
    processing_time_ms: float,
    db: Session
):
    """Save AI analysis log for audit trail"""
    try:
        log_query = text("""
            INSERT INTO ai_analysis_logs 
            (patient_id, medical_record_id, analysis_type, input_data, ai_response, 
             confidence_score, processing_time_ms, ai_model_version)
            VALUES (:patient_id, :medical_record_id, :analysis_type, :input_data, 
                    :ai_response, :confidence_score, :processing_time_ms, :ai_model_version)
        """)
        
        db.execute(log_query, {
            "patient_id": patient_id,
            "medical_record_id": medical_record_id,
            "analysis_type": analysis_type,
            "input_data": json.dumps(input_data),
            "ai_response": json.dumps(ai_response),
            "confidence_score": confidence_score,
            "processing_time_ms": processing_time_ms,
            "ai_model_version": ai_response.get("model_version", "unknown")
        })
        db.commit()
        
    except Exception as e:
        logger.error(f"Error saving AI analysis log: {e}")
        db.rollback()

# ===== API ENDPOINTS =====

@router.post("/analyze/drug-interactions", response_model=DrugInteractionResponse)
async def analyze_drug_interactions(
    request: DrugInteractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED Drug Interaction Analysis
    - Database lookup + AI enhancement
    - Caching for performance
    - Patient-specific contraindications
    """
    start_time = time.time()
    
    try:
        # 1. Generate cache hash
        drug_hash = generate_drug_combination_hash(request.medications)
        
        # 2. Check cache if enabled
        cached_result = None
        if request.include_cache:
            cached_result = await get_cached_interaction_result(drug_hash, db)
        
        if cached_result:
            # Return cached result
            processing_time = (time.time() - start_time) * 1000
            cached_result["result"]["processing_time_ms"] = processing_time
            cached_result["result"]["cache_used"] = True
            
            logger.info(f"Drug interaction analysis completed from cache in {processing_time:.2f}ms")
            return DrugInteractionResponse(**cached_result["result"])
        
        # 3. Analyze interactions from database
        interactions = await analyze_drug_interactions_db(request.medications, db)
        
        # 4. Get patient-specific data if patient_id provided
        patient_allergies = []
        contraindications = []
        
        if request.patient_id:
            patient_allergies = await get_patient_allergies(request.patient_id, db)
            
            # Get medical history for contraindication checking
            patient_query = text("""
                SELECT medical_history FROM patients 
                WHERE id = :patient_id
            """)
            patient_data = db.execute(patient_query, {"patient_id": request.patient_id}).fetchone()
            
            medical_history = []
            if patient_data and patient_data.medical_history:
                try:
                    history_data = json.loads(patient_data.medical_history)
                    medical_history = history_data.get("medical_history", [])
                except:
                    pass
            
            contraindications = await check_contraindications(
                request.medications, 
                patient_allergies, 
                medical_history
            )
        
        # 5. Calculate risk metrics
        high_risk_count = len([i for i in interactions if i.severity == InteractionSeverity.MAJOR])
        
        # 6. Prepare AI analysis if interactions found
        ai_analysis = None
        if interactions or contraindications:
            ai_input = {
                "medications": request.medications,
                "interactions_found": len(interactions),
                "contraindications": contraindications,
                "patient_allergies": patient_allergies
            }
            ai_analysis = await call_ai_analysis(ai_input, "drug_interaction")
        
        # 7. Prepare response
        response_data = {
            "input_medications": request.medications,
            "total_interactions": len(interactions),
            "high_risk_interactions": high_risk_count,
            "interactions": interactions,
            "patient_allergies": patient_allergies,
            "contraindications": contraindications,
            "processing_time_ms": (time.time() - start_time) * 1000,
            "cache_used": False,
            "ai_analysis": ai_analysis
        }
        
        # 8. Save to cache (background task)
        if len(interactions) > 0:
            severity_max = max([i.severity.value for i in interactions])
            background_tasks.add_task(
                save_interaction_cache,
                drug_hash,
                request.medications,
                response_data,
                severity_max,
                db
            )
        
        # 9. Log AI analysis (background task)
        if request.patient_id and ai_analysis:
            background_tasks.add_task(
                save_ai_analysis_log,
                request.patient_id,
                None,
                "drug_interaction",
                ai_input,
                ai_analysis,
                ai_analysis.get("confidence", 0.0),
                response_data["processing_time_ms"],
                db
            )
        
        processing_time = response_data["processing_time_ms"]
        logger.info(f"Drug interaction analysis completed in {processing_time:.2f}ms")
        
        return DrugInteractionResponse(**response_data)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in drug interaction analysis: {e}")
        raise HTTPException(status_code=500, detail="Gagal menganalisis interaksi obat")

@router.post("/analyze/ai-diagnosis", response_model=AIAnalysisResponse)
async def ai_diagnosis_analysis(
    request: AIAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED AI Diagnosis Analysis
    - Comprehensive patient context
    - Multi-modal analysis (symptoms + vitals + history)
    - Treatment recommendations
    """
    start_time = time.time()
    
    try:
        # 1. Validate patient exists and get additional data
        patient_query = text("""
            SELECT p.*, 
                   COUNT(mr.id) as visit_count,
                   MAX(mr.created_at) as last_visit
            FROM patients p
            LEFT JOIN medical_records mr ON p.id = mr.patient_id
            WHERE p.id = :patient_id
            GROUP BY p.id
        """)
        
        patient_data = db.execute(patient_query, {"patient_id": request.patient_id}).fetchone()
        
        if not patient_data:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        # 2. Gather comprehensive patient context
        patient_context = {
            "age": request.age or patient_data.age,
            "gender": request.gender or patient_data.gender,
            "weight_kg": request.weight_kg or patient_data.weight_kg,
            "visit_count": patient_data.visit_count,
            "last_visit": patient_data.last_visit.isoformat() if patient_data.last_visit else None
        }
        
        # 3. Get recent medical history
        history_query = text("""
            SELECT diagnosis_text, medications, symptoms, created_at
            FROM medical_records 
            WHERE patient_id = :patient_id
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        recent_history = db.execute(history_query, {"patient_id": request.patient_id}).fetchall()
        
        # 4. Prepare AI input data
        ai_input = {
            "patient_context": patient_context,
            "current_symptoms": request.symptoms,
            "chief_complaint": request.chief_complaint,
            "vital_signs": request.vital_signs,
            "medical_history": request.medical_history,
            "current_medications": request.current_medications,
            "allergies": request.allergies,
            "recent_visits": [
                {
                    "diagnosis": record.diagnosis_text,
                    "medications": json.loads(record.medications or "[]"),
                    "symptoms": json.loads(record.symptoms or "[]"),
                    "date": record.created_at.isoformat()
                }
                for record in recent_history
            ]
        }
        
        # 5. Call AI service for analysis
        ai_response = await call_ai_analysis(ai_input, request.analysis_type.value)
        
        # 6. Analyze drug interactions if medications provided
        drug_interaction_analysis = None
        if request.current_medications:
            interaction_request = DrugInteractionRequest(
                medications=request.current_medications,
                patient_id=request.patient_id,
                include_cache=True
            )
            # Call the drug interaction endpoint internally
            drug_interaction_analysis = await analyze_drug_interactions(
                interaction_request, background_tasks, db
            )
        
        # 7. Calculate risk assessment
        risk_level = "low"
        risk_factors = []
        
        if request.vital_signs:
            if request.vital_signs.get("temperature", 0) > 38.5:
                risk_factors.append("High fever detected")
                risk_level = "medium"
            if request.vital_signs.get("oxygen_saturation", 100) < 95:
                risk_factors.append("Low oxygen saturation")
                risk_level = "high"
        
        if drug_interaction_analysis and drug_interaction_analysis.high_risk_interactions > 0:
            risk_factors.append(f"{drug_interaction_analysis.high_risk_interactions} major drug interactions")
            risk_level = "high"
        
        # 8. Generate treatment recommendations
        treatment_recommendations = []
        monitoring_recommendations = []
        
        if ai_response.get("ai_recommendations"):
            treatment_recommendations.extend(ai_response["ai_recommendations"])
        
        if risk_level in ["medium", "high"]:
            monitoring_recommendations.append("Monitor patient closely")
            monitoring_recommendations.append("Schedule follow-up within 24-48 hours")
        
        if drug_interaction_analysis and drug_interaction_analysis.contraindications:
            monitoring_recommendations.append("Review medication allergies and contraindications")
        
        # 9. Prepare response
        response_data = {
            "patient_id": request.patient_id,
            "analysis_type": request.analysis_type.value,
            "confidence_score": ai_response.get("confidence", 0.0),
            "suggested_diagnoses": ai_response.get("suggested_diagnoses", []),
            "differential_diagnoses": [],  # To be enhanced
            "drug_interactions": drug_interaction_analysis,
            "treatment_recommendations": treatment_recommendations,
            "monitoring_recommendations": monitoring_recommendations,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "ai_model_version": ai_response.get("model_version", "unknown"),
            "processing_time_ms": (time.time() - start_time) * 1000,
            "created_at": datetime.now()
        }
        
        # 10. Save AI analysis log (background task)
        background_tasks.add_task(
            save_ai_analysis_log,
            request.patient_id,
            None,  # No specific medical record ID
            request.analysis_type.value,
            ai_input,
            ai_response,
            response_data["confidence_score"],
            response_data["processing_time_ms"],
            db
        )
        
        processing_time = response_data["processing_time_ms"]
        logger.info(f"AI diagnosis analysis completed in {processing_time:.2f}ms")
        
        return AIAnalysisResponse(**response_data)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in AI diagnosis analysis: {e}")
        raise HTTPException(status_code=500, detail="Gagal melakukan analisis AI diagnosis")

@router.get("/analyze/history/{patient_id}")
async def get_ai_analysis_history(
    patient_id: int,
    analysis_type: Optional[AIAnalysisType] = Query(None, description="Filter by analysis type"),
    limit: int = Query(10, ge=1, le=50, description="Number of records"),
    db: Session = Depends(get_db)
):
    """Get AI analysis history for a patient"""
    try:
        # Build query conditions
        where_conditions = ["patient_id = :patient_id"]
        params = {"patient_id": patient_id, "limit": limit}
        
        if analysis_type:
            where_conditions.append("analysis_type = :analysis_type")
            params["analysis_type"] = analysis_type.value
        
        where_clause = " AND ".join(where_conditions)
        
        history_query = text(f"""
            SELECT *
            FROM ai_analysis_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        history = db.execute(history_query, params).fetchall()
        
        # Format results
        formatted_history = []
        for record in history:
            formatted_record = {
                "id": record.id,
                "analysis_type": record.analysis_type,
                "confidence_score": float(record.confidence_score) if record.confidence_score else 0.0,
                "processing_time_ms": record.processing_time_ms,
                "ai_model_version": record.ai_model_version,
                "created_at": record.created_at,
                "input_summary": "Complex analysis data",  # Simplified for response
                "ai_response_summary": "AI recommendations available"  # Simplified for response
            }
            formatted_history.append(formatted_record)
        
        return {
            "patient_id": patient_id,
            "total_analyses": len(formatted_history),
            "analysis_history": formatted_history
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting AI analysis history: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil riwayat analisis AI")

@router.get("/analyze/stats/summary")
async def get_ai_analysis_statistics(
    days: int = Query(30, ge=1, le=365, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get AI analysis statistics for dashboard"""
    try:
        stats_query = text("""
            SELECT 
                analysis_type,
                COUNT(*) as total_analyses,
                AVG(confidence_score) as avg_confidence,
                AVG(processing_time_ms) as avg_processing_time,
                COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_confidence_count
            FROM ai_analysis_logs
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY analysis_type
        """)
        
        stats = db.execute(stats_query, {"days": days}).fetchall()
        
        # Cache statistics
        cache_stats_query = text("""
            SELECT 
                COUNT(*) as total_cached_interactions,
                COUNT(CASE WHEN last_checked >= DATE_SUB(NOW(), INTERVAL :days DAY) THEN 1 END) as recent_cache_hits
            FROM drug_interaction_cache
        """)
        
        cache_stats = db.execute(cache_stats_query, {"days": days}).fetchone()
        
        # Format response
        analysis_stats = {}
        for stat in stats:
            analysis_stats[stat.analysis_type] = {
                "total_analyses": stat.total_analyses,
                "avg_confidence": round(float(stat.avg_confidence or 0), 2),
                "avg_processing_time_ms": round(float(stat.avg_processing_time or 0), 2),
                "high_confidence_count": stat.high_confidence_count
            }
        
        return {
            "period_days": days,
            "analysis_statistics": analysis_stats,
            "cache_statistics": {
                "total_cached_interactions": cache_stats.total_cached_interactions,
                "recent_cache_hits": cache_stats.recent_cache_hits,
                "cache_hit_rate": "N/A"  # Would need more data to calculate
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting AI analysis stats: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil statistik analisis AI")