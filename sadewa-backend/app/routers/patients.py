# app/routers/patients.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== SCHEMAS =====

class MedicationData(BaseModel):
    """Schema untuk medication"""
    name: str
    dosage: str
    frequency: str
    notes: Optional[str] = ""

class SaveDiagnosisRequest(BaseModel):
    """Schema untuk save diagnosis"""
    diagnosis_code: str = Field(..., description="ICD-10 code")
    diagnosis_text: str = Field(..., description="Diagnosis description")
    medications: List[MedicationData] = Field(default=[], description="Medications prescribed")
    notes: Optional[str] = Field("", description="Additional notes")
    interactions: Optional[Dict[str, Any]] = Field(None, description="Drug interaction analysis")

# ===== ENDPOINT =====

@router.post("/patients/{no_rm}/save-diagnosis")
async def save_diagnosis(
    no_rm: str,
    request: SaveDiagnosisRequest,
    db: Session = Depends(get_db)
):
    """
    ✅ FIXED: Save diagnosis menggunakan no_rm saja (tanpa patient_id)
    """
    try:
        logger.info(f"DEBUG - Received request for patient {no_rm}")
        
        # 1. Validate patient exists by no_rm
        patient_query = text("SELECT no_rm, name FROM patients WHERE no_rm = :no_rm")
        patient = db.execute(patient_query, {"no_rm": no_rm}).fetchone()
        
        if not patient:
            logger.error(f"Patient {no_rm} not found")
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        logger.info(f"DEBUG - Patient found: {patient.name}")
        
        # 2. Prepare medication data
        medications_json = json.dumps([med.dict() for med in request.medications])
        interactions_json = json.dumps(request.interactions) if request.interactions else None
        
        # 3. ✅ FIXED: Insert with no_rm only (no patient_id)
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
        
        # 4. ✅ NEW: Also add medications to patient_medications table
        if request.medications:
            try:
                await save_patient_medications(no_rm, request.medications, new_record_id, db)
                logger.info(f"DEBUG - {len(request.medications)} medications added to patient_medications")
            except Exception as med_error:
                logger.warning(f"Failed to save patient medications: {med_error}")
                # Don't fail the whole request if medication saving fails
        
        # 5. Return success response
        return {
            "success": True,
            "message": "Diagnosis saved successfully",
            "medical_record_id": new_record_id,
            "patient_no_rm": no_rm,
            "diagnosis": {
                "code": request.diagnosis_code,
                "text": request.diagnosis_text
            },
            "medications_count": len(request.medications),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"ERROR - Save diagnosis failed for {no_rm}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save diagnosis: {str(e)}")

async def save_patient_medications(
    no_rm: str, 
    medications: List[MedicationData], 
    medical_record_id: int, 
    db: Session
):
    """Save medications to patient_medications table"""
    try:
        for med in medications:
            # Insert or update patient medication
            medication_query = text("""
                INSERT INTO patient_medications (
                    no_rm, 
                    medication_name, 
                    dosage, 
                    frequency, 
                    status, 
                    prescribed_by, 
                    medical_record_id,
                    notes,
                    start_date,
                    created_at
                ) VALUES (
                    :no_rm, 
                    :medication_name, 
                    :dosage, 
                    :frequency, 
                    'active', 
                    'System', 
                    :medical_record_id,
                    :notes,
                    CURDATE(),
                    NOW()
                )
                ON DUPLICATE KEY UPDATE
                    dosage = VALUES(dosage),
                    frequency = VALUES(frequency),
                    medical_record_id = VALUES(medical_record_id),
                    status = 'active',
                    updated_at = NOW()
            """)
            
            db.execute(medication_query, {
                "no_rm": no_rm,
                "medication_name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "medical_record_id": medical_record_id,
                "notes": med.notes
            })
        
        db.commit()
        logger.info(f"Successfully saved {len(medications)} medications for patient {no_rm}")
        
    except Exception as e:
        logger.error(f"Failed to save medications for {no_rm}: {e}")
        db.rollback()
        raise

# ===== ADDITIONAL HELPER ENDPOINTS =====

@router.get("/patients/{no_rm}/medical-history")
async def get_patient_medical_history(
    no_rm: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get patient medical history using no_rm"""
    try:
        # Get patient info
        patient_query = text("SELECT no_rm, name FROM patients WHERE no_rm = :no_rm")
        patient = db.execute(patient_query, {"no_rm": no_rm}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        # Get medical records
        records_query = text("""
            SELECT 
                mr.id,
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
async def get_current_medications(
    no_rm: str,
    db: Session = Depends(get_db)
):
    """Get current active medications for patient"""
    try:
        # Validate patient exists
        patient_query = text("SELECT no_rm, name FROM patients WHERE no_rm = :no_rm")
        patient = db.execute(patient_query, {"no_rm": no_rm}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        # Get current medications
        medications_query = text("""
            SELECT 
                id,
                medication_name,
                dosage,
                frequency,
                start_date,
                end_date,
                status,
                prescribed_by,
                notes,
                created_at
            FROM patient_medications
            WHERE no_rm = :no_rm 
              AND status = 'active'
              AND (end_date IS NULL OR end_date > CURDATE())
            ORDER BY start_date DESC
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
                "start_date": med.start_date.isoformat() if med.start_date else None,
                "end_date": med.end_date.isoformat() if med.end_date else None,
                "status": med.status,
                "prescribed_by": med.prescribed_by,
                "notes": med.notes,
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

# ===== TESTING ENDPOINT =====

@router.post("/test-save-diagnosis")
async def test_save_diagnosis(db: Session = Depends(get_db)):
    """Test save diagnosis endpoint"""
    try:
        # Create test request
        test_request = SaveDiagnosisRequest(
            diagnosis_code="G43.0",
            diagnosis_text="Migraine without aura",
            medications=[
                MedicationData(
                    name="Paracetamol",
                    dosage="500mg",
                    frequency="3x daily",
                    notes="Take after meals"
                )
            ],
            notes="Test diagnosis from API",
            interactions={"test": "interaction_data"}
        )
        
        # Use test patient
        test_no_rm = "rm0001"
        
        result = await save_diagnosis(test_no_rm, test_request, db)
        
        return {
            "test_status": "success",
            "result": result
        }
        
    except Exception as e:
        return {
            "test_status": "failed",
            "error": str(e)
        }