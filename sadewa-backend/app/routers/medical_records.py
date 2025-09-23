# app/routers/medical_records_fix.py
"""
✅ FIXED: Medical records router yang menggunakan no_rm saja
Mengatasi error "Unknown column 'patient_id'"
"""

import time
import json
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== SCHEMAS =====

class MedicationData(BaseModel):
    """Schema untuk medication"""
    name: str = Field(..., description="Nama obat")
    dosage: str = Field(..., description="Dosis obat")
    frequency: str = Field(..., description="Frekuensi minum")
    notes: Optional[str] = Field("", description="Catatan obat")

class SaveDiagnosisRequest(BaseModel):
    """Schema untuk save diagnosis"""
    diagnosis_code: str = Field(..., description="ICD-10 code")
    diagnosis_text: str = Field(..., description="Diagnosis description")
    medications: List[MedicationData] = Field(default=[], description="Medications prescribed")
    notes: Optional[str] = Field("", description="Additional notes")
    interactions: Optional[Dict[str, Any]] = Field(None, description="Drug interaction analysis")

class PatientResponse(BaseModel):
    """Patient response schema"""
    no_rm: str
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    weight_kg: Optional[int] = None

class MedicalRecordResponse(BaseModel):
    """Medical record response schema"""
    id: int
    no_rm: str
    diagnosis_code: Optional[str]
    diagnosis_text: Optional[str]
    medications: List[Dict[str, Any]]
    interactions: Optional[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

# ===== ENDPOINTS =====

@router.post("/patients/{no_rm}/save-diagnosis")
async def save_diagnosis_fixed(
    no_rm: str,
    request: SaveDiagnosisRequest,
    db: Session = Depends(get_db)
):
    """
    ✅ FIXED: Save diagnosis menggunakan no_rm saja
    Mengatasi error "Unknown column 'patient_id'"
    """
    start_time = time.time()
    
    try:
        logger.info(f"DEBUG - Received request for patient {no_rm}")
        
        # 1. Validate patient exists by no_rm
        patient_query = text("SELECT no_rm, name FROM patients WHERE no_rm = :no_rm")
        patient = db.execute(patient_query, {"no_rm": no_rm}).fetchone()
        
        if not patient:
            logger.error(f"Patient {no_rm} not found")
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        logger.info(f"DEBUG - Patient found: {patient.name}")
        
        # 2. Prepare data
        medications_json = json.dumps([med.dict() for med in request.medications])
        interactions_json = json.dumps(request.interactions) if request.interactions else None
        
        # 3. ✅ FIXED: Insert dengan schema yang benar (no_rm saja)
        insert_query = text("""
            INSERT INTO medical_records (
                no_rm, 
                diagnosis_code, 
                diagnosis_text, 
                medications, 
                interactions, 
                notes,
                created_at,
                updated_at
            ) VALUES (
                :no_rm, 
                :diagnosis_code, 
                :diagnosis_text, 
                :medications, 
                :interactions, 
                :notes,
                NOW(),
                NOW()
            )
        """)
        
        # Execute insert
        result = db.execute(insert_query, {
            "no_rm": no_rm,
            "diagnosis_code": request.diagnosis_code,
            "diagnosis_text": request.diagnosis_text,
            "medications": medications_json,
            "interactions": interactions_json,
            "notes": request.notes
        })
        
        new_record_id = result.lastrowid
        db.commit()
        
        logger.info(f"DEBUG - Medical record saved with ID: {new_record_id}")
        
        # 4. ✅ NEW: Save to patient_medications table
        if request.medications:
            try:
                await save_patient_medications_fixed(no_rm, request.medications, new_record_id, db)
                logger.info(f"DEBUG - {len(request.medications)} medications saved to patient_medications")
            except Exception as med_error:
                logger.warning(f"Failed to save patient medications: {med_error}")
        
        # 5. Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # 6. Return success response
        return {
            "success": True,
            "message": "Diagnosis saved successfully",
            "data": {
                "medical_record_id": new_record_id,
                "patient_no_rm": no_rm,
                "patient_name": patient.name,
                "diagnosis": {
                    "code": request.diagnosis_code,
                    "text": request.diagnosis_text
                },
                "medications_count": len(request.medications),
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR - Save diagnosis failed for {no_rm}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save diagnosis: {str(e)}")

async def save_patient_medications_fixed(
    no_rm: str, 
    medications: List[MedicationData], 
    medical_record_id: int, 
    db: Session
):
    """✅ FIXED: Save medications to patient_medications table using no_rm"""
    try:
        for med in medications:
            medication_query = text("""
                INSERT INTO patient_medications (
                    no_rm, 
                    medication_name, 
                    dosage, 
                    frequency, 
                    is_active,
                    created_at
                ) VALUES (
                    :no_rm, 
                    :medication_name, 
                    :dosage, 
                    :frequency, 
                    1,
                    NOW()
                )
                ON DUPLICATE KEY UPDATE
                    dosage = VALUES(dosage),
                    frequency = VALUES(frequency),
                    is_active = 1
            """)
            
            db.execute(medication_query, {
                "no_rm": no_rm,
                "medication_name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency
            })
        
        db.commit()
        logger.info(f"Successfully saved {len(medications)} medications for patient {no_rm}")
        
    except Exception as e:
        logger.error(f"Failed to save medications for {no_rm}: {e}")
        db.rollback()
        raise

@router.get("/patients/{no_rm}/medical-history")
async def get_medical_history_fixed(
    no_rm: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """✅ FIXED: Get medical history using no_rm"""
    try:
        # Validate patient
        patient_query = text("SELECT no_rm, name FROM patients WHERE no_rm = :no_rm")
        patient = db.execute(patient_query, {"no_rm": no_rm}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        # Get medical records
        records_query = text("""
            SELECT 
                mr.id,
                mr.no_rm,
                mr.diagnosis_code,
                mr.diagnosis_text,
                mr.medications,
                mr.interactions,
                mr.notes,
                mr.created_at,
                mr.updated_at
            FROM medical_records mr
            WHERE mr.no_rm = :no_rm
            ORDER BY mr.created_at DESC
            LIMIT :limit
        """)
        
        records = db.execute(records_query, {"no_rm": no_rm, "limit": limit}).fetchall()
        
        # Format records
        formatted_records = []
        for record in records:
            medications = json.loads(record.medications) if record.medications else []
            interactions = json.loads(record.interactions) if record.interactions else {}
            
            formatted_records.append({
                "id": record.id,
                "no_rm": record.no_rm,
                "diagnosis_code": record.diagnosis_code,
                "diagnosis_text": record.diagnosis_text,
                "medications": medications,
                "interactions": interactions,
                "notes": record.notes,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            })
        
        return {
            "success": True,
            "patient": {
                "no_rm": patient.no_rm,
                "name": patient.name
            },
            "medical_records": formatted_records,
            "total_records": len(formatted_records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medical history for {no_rm}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get medical history: {str(e)}")

@router.get("/patients/{no_rm}/current-medications")
async def get_current_medications_fixed(
    no_rm: str,
    db: Session = Depends(get_db)
):
    """✅ FIXED: Get current medications using no_rm"""
    try:
        # Validate patient
        patient_query = text("SELECT no_rm, name FROM patients WHERE no_rm = :no_rm")
        patient = db.execute(patient_query, {"no_rm": no_rm}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        # Get current medications from patient_medications table
        medications_query = text("""
            SELECT 
                id,
                medication_name,
                dosage,
                frequency,
                is_active,
                created_at
            FROM patient_medications
            WHERE no_rm = :no_rm 
              AND is_active = 1
            ORDER BY created_at DESC
        """)
        
        medications = db.execute(medications_query, {"no_rm": no_rm}).fetchall()
        
        # Format medications
        formatted_medications = []
        for med in medications:
            formatted_medications.append({
                "id": med.id,
                "name": med.medication_name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "is_active": med.is_active,
                "created_at": med.created_at.isoformat() if med.created_at else None
            })
        
        return {
            "success": True,
            "patient": {
                "no_rm": patient.no_rm,
                "name": patient.name
            },
            "current_medications": formatted_medications,
            "total_medications": len(formatted_medications)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current medications for {no_rm}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current medications: {str(e)}")

# ===== TESTING ENDPOINTS =====

@router.post("/test-save-diagnosis")
async def test_save_diagnosis_fixed(db: Session = Depends(get_db)):
    """Test save diagnosis dengan data mock"""
    try:
        test_request = SaveDiagnosisRequest(
            diagnosis_code="G43.0",
            diagnosis_text="Migrain tanpa aura",
            medications=[
                MedicationData(
                    name="Paracetamol",
                    dosage="500mg",
                    frequency="3x sehari",
                    notes="Sesudah makan"
                )
            ],
            notes="Test diagnosis from fixed API",
            interactions={"test": "interaction_data", "risk_level": "LOW"}
        )
        
        # Use existing patient
        test_no_rm = "rm0001"
        
        result = await save_diagnosis_fixed(test_no_rm, test_request, db)
        
        return {
            "test_status": "success",
            "message": "Fixed save diagnosis is working",
            "result": result
        }
        
    except Exception as e:
        return {
            "test_status": "failed",
            "error": str(e),
            "message": "Test failed - check logs for details"
        }

@router.get("/check-medical-records-schema")
async def check_schema(db: Session = Depends(get_db)):
    """Check medical_records table schema"""
    try:
        schema_query = text("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'medical_records' 
            AND TABLE_SCHEMA = DATABASE()
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = db.execute(schema_query).fetchall()
        
        schema_info = []
        for col in columns:
            schema_info.append({
                "column_name": col.COLUMN_NAME,
                "data_type": col.DATA_TYPE,
                "is_nullable": col.IS_NULLABLE
            })
        
        return {
            "table": "medical_records",
            "columns": schema_info,
            "has_patient_id": any(col["column_name"] == "patient_id" for col in schema_info),
            "has_no_rm": any(col["column_name"] == "no_rm" for col in schema_info)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to check schema"
        }