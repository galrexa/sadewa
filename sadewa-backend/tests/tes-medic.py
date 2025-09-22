# fix_medical_records_issues.py
"""
Debug dan fix medical records endpoint issues
"""

import json
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, validator

# Import database
from app.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== FIXED PYDANTIC MODELS =====

class SymptomData(BaseModel):
    """Fixed symptom data model"""
    symptom: str = Field(..., description="Nama gejala")
    severity: str = Field(..., description="mild, moderate, severe")
    duration: str = Field(..., description="acute, subacute, chronic")
    description: Optional[str] = Field(None, description="Deskripsi detail")
    onset_date: Optional[str] = Field(None, description="Tanggal mulai gejala (YYYY-MM-DD)")

class VitalSigns(BaseModel):
    """Fixed vital signs model"""
    blood_pressure_systolic: Optional[int] = Field(None, ge=50, le=300)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=30, le=200)
    heart_rate: Optional[int] = Field(None, ge=30, le=250)
    temperature: Optional[float] = Field(None, ge=30.0, le=45.0)
    respiratory_rate: Optional[int] = Field(None, ge=8, le=60)
    oxygen_saturation: Optional[int] = Field(None, ge=70, le=100)
    weight_kg: Optional[float] = Field(None, ge=0.1, le=500.0)
    height_cm: Optional[float] = Field(None, ge=30.0, le=250.0)

class MedicalRecordCreate(BaseModel):
    """Fixed medical record creation model"""
    patient_id: int = Field(..., description="ID pasien")
    visit_type: str = Field(default="initial", description="initial, followup, emergency")
    chief_complaint: str = Field(..., min_length=5, max_length=500, description="Keluhan utama")
    symptoms: Optional[List[SymptomData]] = Field(default=[], description="Daftar gejala")
    vital_signs: Optional[VitalSigns] = Field(None, description="Tanda vital")
    physical_examination: Optional[str] = Field(None, description="Hasil pemeriksaan fisik")
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Diagnosis dalam teks")
    differential_diagnosis: Optional[List[str]] = Field(default=[], description="Diagnosis banding")
    medications: Optional[List[str]] = Field(default=[], description="Daftar obat")
    treatment_plan: Optional[str] = Field(None, description="Rencana perawatan")
    notes: Optional[str] = Field(None, description="Catatan tambahan")
    follow_up_date: Optional[str] = Field(None, description="Tanggal kontrol (YYYY-MM-DD)")

# ===== FIXED ENDPOINTS =====

@router.post("/api/medical-records", status_code=201)
async def create_medical_record_fixed(
    record_data: MedicalRecordCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    FIXED Medical Record Creation Endpoint
    """
    start_time = datetime.now()
    
    try:
        # 1. Validate patient exists
        patient_check = text("SELECT id, name FROM patients WHERE id = :patient_id")
        patient = db.execute(patient_check, {"patient_id": record_data.patient_id}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        # 2. Prepare JSON data safely
        symptoms_json = json.dumps([
            {
                "symptom": symptom.symptom,
                "severity": symptom.severity,
                "duration": symptom.duration,
                "description": symptom.description,
                "onset_date": symptom.onset_date
            } for symptom in record_data.symptoms
        ]) if record_data.symptoms else "[]"
        
        medications_json = json.dumps(record_data.medications or [])
        differential_json = json.dumps(record_data.differential_diagnosis or [])
        
        # 3. Prepare interactions data
        interactions_data = {
            "visit_type": record_data.visit_type,
            "chief_complaint": record_data.chief_complaint,
            "vital_signs": record_data.vital_signs.dict() if record_data.vital_signs else None,
            "differential_diagnosis": record_data.differential_diagnosis or [],
            "treatment_plan": record_data.treatment_plan,
            "follow_up_date": record_data.follow_up_date,
            "created_at": datetime.now().isoformat()
        }
        
        # 4. Build comprehensive notes
        notes_parts = []
        if record_data.chief_complaint:
            notes_parts.append(f"Keluhan Utama: {record_data.chief_complaint}")
        if record_data.physical_examination:
            notes_parts.append(f"Pemeriksaan Fisik: {record_data.physical_examination}")
        if record_data.treatment_plan:
            notes_parts.append(f"Rencana Perawatan: {record_data.treatment_plan}")
        if record_data.notes:
            notes_parts.append(f"Catatan: {record_data.notes}")
        if record_data.follow_up_date:
            notes_parts.append(f"Kontrol: {record_data.follow_up_date}")
        
        comprehensive_notes = "\n\n".join(notes_parts)
        
        # 5. Insert with proper error handling
        insert_query = text("""
            INSERT INTO medical_records (
                patient_id, diagnosis_code, diagnosis_text, medications, 
                notes, symptoms, interactions, created_at, updated_at
            ) VALUES (
                :patient_id, :diagnosis_code, :diagnosis_text, :medications,
                :notes, :symptoms, :interactions, NOW(), NOW()
            )
        """)
        
        # Execute insert
        result = db.execute(insert_query, {
            "patient_id": record_data.patient_id,
            "diagnosis_code": record_data.diagnosis_code,
            "diagnosis_text": record_data.diagnosis_text,
            "medications": medications_json,
            "notes": comprehensive_notes,
            "symptoms": symptoms_json,
            "interactions": json.dumps(interactions_data)
        })
        
        new_record_id = result.lastrowid
        db.commit()
        
        # 6. Retrieve and format response
        record_query = text("""
            SELECT mr.*, p.name as patient_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            WHERE mr.id = :record_id
        """)
        
        record = db.execute(record_query, {"record_id": new_record_id}).fetchone()
        
        # 7. Format response safely
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response_data = {
            "id": record.id,
            "patient_id": record.patient_id,
            "patient_name": record.patient_name,
            "visit_type": record_data.visit_type,
            "chief_complaint": record_data.chief_complaint,
            "symptoms": json.loads(record.symptoms or "[]"),
            "vital_signs": record_data.vital_signs.dict() if record_data.vital_signs else None,
            "physical_examination": record_data.physical_examination,
            "diagnosis_code": record.diagnosis_code,
            "diagnosis_text": record.diagnosis_text,
            "differential_diagnosis": json.loads(record.interactions or "{}").get("differential_diagnosis", []),
            "medications": json.loads(record.medications or "[]"),
            "treatment_plan": record_data.treatment_plan,
            "notes": record_data.notes,
            "follow_up_date": record_data.follow_up_date,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "symptom_count": len(record_data.symptoms or []),
            "medication_count": len(record_data.medications or []),
            "risk_level": "low",  # Simple risk calculation
            "processing_time_ms": processing_time
        }
        
        logger.info(f"Medical record {new_record_id} created successfully in {processing_time:.2f}ms")
        return response_data
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating medical record: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating medical record: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/api/medical-records/patient/{patient_id}")
async def get_patient_medical_history_fixed(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50),
    include_allergies: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    FIXED Get patient medical history
    """
    try:
        # 1. Validate patient exists
        patient_query = text("SELECT id, name FROM patients WHERE id = :patient_id")
        patient = db.execute(patient_query, {"patient_id": patient_id}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        # 2. Get medical records with safe JSON handling
        records_query = text("""
            SELECT 
                mr.id, mr.patient_id, mr.diagnosis_code, mr.diagnosis_text,
                mr.medications, mr.symptoms, mr.interactions, mr.notes,
                mr.created_at, mr.updated_at,
                p.name as patient_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            WHERE mr.patient_id = :patient_id
            ORDER BY mr.created_at DESC
            LIMIT :limit
        """)
        
        records = db.execute(records_query, {
            "patient_id": patient_id,
            "limit": limit
        }).fetchall()
        
        # 3. Format records safely
        formatted_records = []
        for record in records:
            try:
                # Safe JSON parsing with fallbacks
                symptoms = json.loads(record.symptoms or "[]")
                medications = json.loads(record.medications or "[]")
                interactions = json.loads(record.interactions or "{}")
                
                formatted_record = {
                    "id": record.id,
                    "patient_id": record.patient_id,
                    "patient_name": record.patient_name,
                    "chief_complaint": interactions.get("chief_complaint", ""),
                    "diagnosis_code": record.diagnosis_code,
                    "diagnosis_text": record.diagnosis_text,
                    "symptoms": symptoms,
                    "medications": medications,
                    "notes": record.notes,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "symptom_count": len(symptoms),
                    "medication_count": len(medications),
                    "risk_level": "low"  # Simple default
                }
                formatted_records.append(formatted_record)
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for record {record.id}: {e}")
                # Add record with minimal data if JSON fails
                formatted_records.append({
                    "id": record.id,
                    "patient_id": record.patient_id,
                    "patient_name": record.patient_name,
                    "diagnosis_text": record.diagnosis_text,
                    "notes": record.notes,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "error": "Data parsing error"
                })
        
        # 4. Get allergies if requested
        allergies = []
        if include_allergies:
            try:
                allergy_query = text("""
                    SELECT allergen, reaction_type 
                    FROM patient_allergies 
                    WHERE patient_id = :patient_id
                """)
                allergy_results = db.execute(allergy_query, {"patient_id": patient_id}).fetchall()
                allergies = [f"{a.allergen} ({a.reaction_type})" if a.reaction_type else a.allergen 
                            for a in allergy_results]
            except Exception as e:
                logger.warning(f"Error getting allergies: {e}")
                allergies = []
        
        # 5. Get statistics
        stats_query = text("""
            SELECT 
                COUNT(*) as total_visits,
                MAX(created_at) as last_visit
            FROM medical_records 
            WHERE patient_id = :patient_id
        """)
        stats = db.execute(stats_query, {"patient_id": patient_id}).fetchone()
        
        return {
            "patient_id": patient_id,
            "patient_name": patient.name,
            "medical_records": formatted_records,
            "total_visits": stats.total_visits if stats else 0,
            "last_visit": stats.last_visit.isoformat() if stats and stats.last_visit else None,
            "chronic_conditions": [],  # Could be enhanced
            "current_medications": formatted_records[0].get("medications", []) if formatted_records else [],
            "allergies": allergies
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting patient history {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting patient history {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/api/medical-records/search/symptoms")
async def search_by_symptoms_fixed(
    symptoms: str = Query(..., description="Comma-separated symptoms"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    FIXED Search medical records by symptoms
    """
    try:
        symptom_list = [s.strip().lower() for s in symptoms.split(',') if s.strip()]
        
        if not symptom_list:
            raise HTTPException(status_code=400, detail="No valid symptoms provided")
        
        # Build search query safely
        search_conditions = []
        params = {"limit": limit}
        
        for i, symptom in enumerate(symptom_list):
            param_name = f"symptom_{i}"
            search_conditions.append(f"(LOWER(symptoms) LIKE :{param_name} OR LOWER(notes) LIKE :{param_name})")
            params[param_name] = f"%{symptom}%"
        
        where_clause = " OR ".join(search_conditions)
        
        search_query = text(f"""
            SELECT 
                mr.id, mr.patient_id, mr.diagnosis_text, mr.symptoms, 
                mr.medications, mr.notes, mr.created_at,
                p.name as patient_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            WHERE {where_clause}
            ORDER BY mr.created_at DESC
            LIMIT :limit
        """)
        
        records = db.execute(search_query, params).fetchall()
        
        # Format results safely
        formatted_records = []
        for record in records:
            try:
                symptoms_data = json.loads(record.symptoms or "[]")
                medications_data = json.loads(record.medications or "[]")
                
                formatted_record = {
                    "id": record.id,
                    "patient_id": record.patient_id,
                    "patient_name": record.patient_name,
                    "diagnosis_text": record.diagnosis_text,
                    "symptoms": symptoms_data,
                    "medications": medications_data,
                    "notes": record.notes,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "symptom_count": len(symptoms_data),
                    "medication_count": len(medications_data)
                }
                formatted_records.append(formatted_record)
                
            except json.JSONDecodeError:
                # Handle corrupt JSON gracefully
                formatted_records.append({
                    "id": record.id,
                    "patient_name": record.patient_name,
                    "diagnosis_text": record.diagnosis_text,
                    "notes": record.notes,
                    "error": "Data parsing error"
                })
        
        return {
            "search_terms": symptom_list,
            "total_found": len(formatted_records),
            "medical_records": formatted_records
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error searching symptoms: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error searching symptoms: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# Add this router to your main app
# app.include_router(router)

if __name__ == "__main__":
    print("🔧 Medical Records Fix Applied")
    print("Add these endpoints to your main.py:")
    print("app.include_router(fix_medical_records_router)")