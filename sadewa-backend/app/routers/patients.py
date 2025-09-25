# app/routers/patients.py
"""
✅ COMPLETE PATIENTS ROUTER - SADEWA Backend
Menggunakan no_rm sebagai primary identifier, sesuai database structure yang ada
Includes: CRUD operations, search, pagination, medical history, medications
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
import logging

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== SCHEMAS =====

class PatientCreate(BaseModel):
    """Schema untuk create patient"""
    no_rm: str = Field(..., description="Nomor Rekam Medis")
    name: str = Field(..., description="Nama lengkap pasien")
    age: int = Field(..., ge=0, le=150, description="Umur pasien")
    gender: str = Field(..., pattern="^(male|female)$", description="Jenis kelamin")
    phone: Optional[str] = Field(None, description="Nomor telepon")
    weight_kg: Optional[int] = Field(None, ge=0, description="Berat badan (kg)")
    medical_history: Optional[Dict[str, Any]] = Field(None, description="Riwayat medis untuk AI analysis")
    risk_factors: Optional[Dict[str, Any]] = Field(None, description="Faktor risiko untuk AI assessment")
    ai_risk_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="AI-generated risk score")
    
class PatientUpdate(BaseModel):
    """Schema untuk update patient"""
    name: Optional[str] = Field(None, description="Nama lengkap pasien")
    age: Optional[int] = Field(None, ge=0, le=150, description="Umur pasien")
    gender: Optional[str] = Field(None, pattern="^(male|female)$", description="Jenis kelamin")
    phone: Optional[str] = Field(None, description="Nomor telepon")
    weight_kg: Optional[int] = Field(None, ge=0, description="Berat badan (kg)")
    medical_history: Optional[Dict[str, Any]] = Field(None, description="Riwayat medis untuk AI analysis")
    risk_factors: Optional[Dict[str, Any]] = Field(None, description="Faktor risiko untuk AI assessment")
    ai_risk_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="AI-generated risk score")

class PatientResponse(BaseModel):
    """Patient response schema"""
    id: int
    no_rm: str
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    weight_kg: Optional[int] = None
    medical_history: Optional[Dict[str, Any]] = None
    risk_factors: Optional[Dict[str, Any]] = None
    last_ai_analysis: Optional[str] = None
    ai_risk_score: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

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

class PaginatedResponse(BaseModel):
    """Schema untuk paginated response"""
    patients: List[PatientResponse]
    total: int
    page: int
    limit: int
    total_pages: int

# ===== GET ENDPOINTS =====

@router.get("/search")
async def search_patients(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    q: Optional[str] = Query(None, description="Search query"),
    db: Session = Depends(get_db)
):
    """
    ✅ FIXED: Search patients dengan pagination
    Mengatasi error 404: GET /api/patients/search
    Response structure sesuai yang diharapkan frontend
    """
    start_time = time.time()
    
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Base query
        base_query = """
            SELECT id, no_rm, name, age, gender, phone, weight_kg,
                   medical_history, risk_factors, last_ai_analysis, ai_risk_score,
                   created_at, updated_at
            FROM patients
        """
        count_query = "SELECT COUNT(*) FROM patients"
        
        # Add search filter if provided
        search_condition = ""
        params = {}
        
        if q and q.strip():
            search_condition = """ WHERE 
                LOWER(name) LIKE :search_term OR 
                LOWER(no_rm) LIKE :search_term OR 
                LOWER(phone) LIKE :search_term
            """
            params["search_term"] = f"%{q.strip().lower()}%"
        
        # Get total count
        total_query = count_query + search_condition
        total_result = db.execute(text(total_query), params).scalar()
        total_patients = total_result if total_result else 0
        
        # Get patients with pagination
        patients_query = f"{base_query}{search_condition} ORDER BY name LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})
        
        patients_result = db.execute(text(patients_query), params).fetchall()
        
        # Format response
        patients_list = []
        for patient in patients_result:
            # Parse JSON fields safely
            medical_history = None
            risk_factors = None
            
            if patient.medical_history:
                try:
                    medical_history = json.loads(patient.medical_history) if isinstance(patient.medical_history, str) else patient.medical_history
                except (json.JSONDecodeError, TypeError):
                    medical_history = None
                    
            if patient.risk_factors:
                try:
                    risk_factors = json.loads(patient.risk_factors) if isinstance(patient.risk_factors, str) else patient.risk_factors
                except (json.JSONDecodeError, TypeError):
                    risk_factors = None
            
            patients_list.append({
                "id": patient.id,
                "no_rm": patient.no_rm,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "phone": patient.phone,
                "weight_kg": patient.weight_kg,
                "medical_history": medical_history,
                "risk_factors": risk_factors,
                "last_ai_analysis": patient.last_ai_analysis.isoformat() if patient.last_ai_analysis else None,
                "ai_risk_score": float(patient.ai_risk_score) if patient.ai_risk_score else None,
                "created_at": patient.created_at.isoformat() if patient.created_at else None,
                "updated_at": patient.updated_at.isoformat() if patient.updated_at else None
            })
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Found {len(patients_list)} patients (page {page}, total {total_patients}) in {processing_time:.3f}s")
        
        return {
            "patients": patients_list,
            "total": total_patients,
            "page": page,
            "limit": limit,
            "total_pages": (total_patients + limit - 1) // limit
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Failed to search patients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search patients: {str(e)}")

@router.get("/")
async def get_all_patients(
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Get all patients (for compatibility with frontend)
    Used by PatientSelector component
    """
    try:
        patients_query = text("""
            SELECT id, no_rm, name, age, gender, phone, weight_kg,
                   medical_history, risk_factors, last_ai_analysis, ai_risk_score,
                   created_at, updated_at
            FROM patients 
            ORDER BY name 
            LIMIT :limit
        """)
        
        patients_result = db.execute(patients_query, {"limit": limit}).fetchall()
        
        # Format response
        patients_list = []
        for patient in patients_result:
            # Parse JSON fields safely
            medical_history = None
            risk_factors = None
            
            if patient.medical_history:
                try:
                    medical_history = json.loads(patient.medical_history) if isinstance(patient.medical_history, str) else patient.medical_history
                except (json.JSONDecodeError, TypeError):
                    medical_history = None
                    
            if patient.risk_factors:
                try:
                    risk_factors = json.loads(patient.risk_factors) if isinstance(patient.risk_factors, str) else patient.risk_factors
                except (json.JSONDecodeError, TypeError):
                    risk_factors = None
            
            patients_list.append({
                "id": patient.id,
                "no_rm": patient.no_rm,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "phone": patient.phone,
                "weight_kg": patient.weight_kg,
                "medical_history": medical_history,
                "risk_factors": risk_factors,
                "last_ai_analysis": patient.last_ai_analysis.isoformat() if patient.last_ai_analysis else None,
                "ai_risk_score": float(patient.ai_risk_score) if patient.ai_risk_score else None,
                "created_at": patient.created_at.isoformat() if patient.created_at else None,
                "updated_at": patient.updated_at.isoformat() if patient.updated_at else None
            })
        
        logger.info(f"✅ Retrieved {len(patients_list)} patients")
        
        return {
            "success": True,
            "data": patients_list,
            "total": len(patients_list)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get all patients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get patients: {str(e)}")

@router.get("/{no_rm}")
async def get_patient_by_no_rm(
    no_rm: str,
    db: Session = Depends(get_db)
):
    """Get patient details by no_rm WITH medical records"""
    try:
        # Get patient basic info
        patient_query = text("""
            SELECT id, no_rm, name, age, gender, phone, weight_kg,
                   medical_history, risk_factors, last_ai_analysis, ai_risk_score,
                   created_at, updated_at
            FROM patients 
            WHERE no_rm = :no_rm
        """)
        
        patient = db.execute(patient_query, {"no_rm": no_rm}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        # Parse JSON fields safely
        medical_history = None
        risk_factors = None
        
        if patient.medical_history:
            try:
                medical_history = json.loads(patient.medical_history) if isinstance(patient.medical_history, str) else patient.medical_history
            except (json.JSONDecodeError, TypeError):
                medical_history = None
                
        if patient.risk_factors:
            try:
                risk_factors = json.loads(patient.risk_factors) if isinstance(patient.risk_factors, str) else patient.risk_factors
            except (json.JSONDecodeError, TypeError):
                risk_factors = None

        # ✅ ADDED: Get medical records
        records_query = text("""
            SELECT 
                id, no_rm, diagnosis_code, diagnosis_text, medications, 
                interactions, notes, created_at, updated_at
            FROM medical_records 
            WHERE no_rm = :no_rm
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        records = db.execute(records_query, {"no_rm": no_rm}).fetchall()
        
        # Format medical records
        medical_records = []
        for record in records:
            medications = json.loads(record.medications) if record.medications else []
            interactions = json.loads(record.interactions) if record.interactions else {}
            
            medical_records.append({
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
        
        patient_data = {
            "id": patient.id,
            "no_rm": patient.no_rm,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "phone": patient.phone,
            "weight_kg": patient.weight_kg,
            "medical_history": medical_history,
            "risk_factors": risk_factors,
            "last_ai_analysis": patient.last_ai_analysis.isoformat() if patient.last_ai_analysis else None,
            "ai_risk_score": float(patient.ai_risk_score) if patient.ai_risk_score else None,
            "created_at": patient.created_at.isoformat() if patient.created_at else None,
            "updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
            "medical_records": medical_records  # ✅ ADDED: Include medical records
        }
        
        logger.info(f"✅ Found patient {no_rm}: {patient.name} with {len(medical_records)} medical records")
        return {"success": True, "data": patient_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get patient {no_rm}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get patient: {str(e)}")

# ===== POST ENDPOINTS =====

@router.post("/")
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    """Create new patient"""
    try:
        # Check if no_rm already exists
        check_query = text("SELECT no_rm FROM patients WHERE no_rm = :no_rm")
        existing = db.execute(check_query, {"no_rm": patient.no_rm}).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail=f"Patient with no_rm {patient.no_rm} already exists")
        
        # Insert new patient
        insert_query = text("""
            INSERT INTO patients (
                no_rm, name, age, gender, phone, weight_kg,
                medical_history, risk_factors, ai_risk_score,
                created_at, updated_at
            ) VALUES (
                :no_rm, :name, :age, :gender, :phone, :weight_kg,
                :medical_history, :risk_factors, :ai_risk_score,
                NOW(), NOW()
            )
        """)
        
        # Prepare JSON fields
        medical_history_json = json.dumps(patient.medical_history) if patient.medical_history else None
        risk_factors_json = json.dumps(patient.risk_factors) if patient.risk_factors else None
        
        db.execute(insert_query, {
            "no_rm": patient.no_rm,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "phone": patient.phone,
            "weight_kg": patient.weight_kg,
            "medical_history": medical_history_json,
            "risk_factors": risk_factors_json,
            "ai_risk_score": patient.ai_risk_score
        })
        
        db.commit()
        
        logger.info(f"✅ Created patient {patient.no_rm}: {patient.name}")
        
        return {
            "success": True,
            "message": f"Patient {patient.name} created successfully",
            "no_rm": patient.no_rm
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create patient: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")

@router.post("/{no_rm}/save-diagnosis")
async def save_diagnosis(
    no_rm: str,
    request: SaveDiagnosisRequest,
    db: Session = Depends(get_db)
):
    """
    ✅ FIXED: Save diagnosis menggunakan no_rm saja (tanpa patient_id)
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
        
        # 2. Prepare medication data
        medications_json = json.dumps([med.dict() for med in request.medications])
        interactions_json = json.dumps(request.interactions) if request.interactions else None
        
        # 3. Insert medical record
        insert_query = text("""
            INSERT INTO medical_records (
                no_rm, diagnosis_code, diagnosis_text, 
                medications, interactions, notes, 
                created_at, updated_at
            ) VALUES (
                :no_rm, :diagnosis_code, :diagnosis_text,
                :medications, :interactions, :notes,
                NOW(), NOW()
            )
        """)
        
        result = db.execute(insert_query, {
            "no_rm": no_rm,
            "diagnosis_code": request.diagnosis_code,
            "diagnosis_text": request.diagnosis_text,
            "medications": medications_json,
            "interactions": interactions_json,
            "notes": request.notes
        })
        
        # Get the inserted record ID
        medical_record_id = result.lastrowid
        logger.info(f"DEBUG - Medical record created with ID: {medical_record_id}")
        
        # 4. Save individual medications to patient_medications table
        if request.medications:
            await _save_patient_medications(db, no_rm, request.medications, medical_record_id)
        
        db.commit()
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Diagnosis saved for patient {no_rm} in {processing_time:.3f}s")
        
        return {
            "success": True,
            "message": f"Diagnosis saved successfully for patient {patient.name}",
            "medical_record_id": medical_record_id,
            "diagnosis": {
                "code": request.diagnosis_code,
                "text": request.diagnosis_text
            },
            "medications_count": len(request.medications),
            "processing_time": f"{processing_time:.3f}s"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        processing_time = time.time() - start_time
        logger.error(f"❌ Failed to save diagnosis for {no_rm}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save diagnosis: {str(e)}")

# ===== PUT ENDPOINTS =====

@router.put("/{no_rm}")
async def update_patient(
    no_rm: str,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db)
):
    """Update patient information"""
    try:
        # Check if patient exists
        check_query = text("SELECT no_rm, name FROM patients WHERE no_rm = :no_rm")
        existing = db.execute(check_query, {"no_rm": no_rm}).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        # Build update query dynamically
        update_fields = []
        params = {"no_rm": no_rm}
        
        if patient_update.name is not None:
            update_fields.append("name = :name")
            params["name"] = patient_update.name
        
        if patient_update.age is not None:
            update_fields.append("age = :age")
            params["age"] = patient_update.age
            
        if patient_update.gender is not None:
            update_fields.append("gender = :gender")
            params["gender"] = patient_update.gender
            
        if patient_update.phone is not None:
            update_fields.append("phone = :phone")
            params["phone"] = patient_update.phone
            
        if patient_update.weight_kg is not None:
            update_fields.append("weight_kg = :weight_kg")
            params["weight_kg"] = patient_update.weight_kg
            
        if patient_update.medical_history is not None:
            update_fields.append("medical_history = :medical_history")
            params["medical_history"] = json.dumps(patient_update.medical_history)
            
        if patient_update.risk_factors is not None:
            update_fields.append("risk_factors = :risk_factors")
            params["risk_factors"] = json.dumps(patient_update.risk_factors)
            
        if patient_update.ai_risk_score is not None:
            update_fields.append("ai_risk_score = :ai_risk_score")
            params["ai_risk_score"] = patient_update.ai_risk_score
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated_at
        update_fields.append("updated_at = NOW()")
        
        # Execute update
        update_query = f"UPDATE patients SET {', '.join(update_fields)} WHERE no_rm = :no_rm"
        db.execute(text(update_query), params)
        db.commit()
        
        logger.info(f"✅ Updated patient {no_rm}")
        
        return {
            "success": True,
            "message": f"Patient {no_rm} updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update patient {no_rm}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update patient: {str(e)}")

# ===== DELETE ENDPOINTS =====

@router.delete("/{no_rm}")
async def delete_patient(
    no_rm: str,
    db: Session = Depends(get_db)
):
    """Delete patient and related records"""
    try:
        # Check if patient exists
        check_query = text("SELECT no_rm, name FROM patients WHERE no_rm = :no_rm")
        existing = db.execute(check_query, {"no_rm": no_rm}).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail=f"Patient {no_rm} not found")
        
        patient_name = existing.name
        
        # Delete related records first (foreign key constraints)
        # Delete patient medications
        db.execute(text("DELETE FROM patient_medications WHERE no_rm = :no_rm"), {"no_rm": no_rm})
        
        # Delete medical records
        db.execute(text("DELETE FROM medical_records WHERE no_rm = :no_rm"), {"no_rm": no_rm})
        
        # Delete patient timeline
        db.execute(text("DELETE FROM patient_timeline WHERE no_rm = :no_rm"), {"no_rm": no_rm})
        
        # Finally delete patient
        db.execute(text("DELETE FROM patients WHERE no_rm = :no_rm"), {"no_rm": no_rm})
        
        db.commit()
        
        logger.info(f"✅ Deleted patient {no_rm}: {patient_name}")
        
        return {
            "success": True,
            "message": f"Patient {patient_name} ({no_rm}) deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete patient {no_rm}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete patient: {str(e)}")

# ===== MEDICAL HISTORY ENDPOINTS =====

@router.get("/{no_rm}/medical-history")
async def get_patient_medical_history(
    no_rm: str,
    limit: int = Query(10, ge=1, le=100, description="Number of records to retrieve"),
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
        logger.error(f"❌ Failed to get medical history for {no_rm}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get medical history: {str(e)}")

@router.get("/{no_rm}/current-medications")
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
        logger.error(f"❌ Failed to get current medications for {no_rm}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current medications: {str(e)}")

@router.get("/stats")
async def get_patients_statistics(db: Session = Depends(get_db)):
    """Get patients statistics"""
    try:
        # Get total patients
        total_query = text("SELECT COUNT(*) FROM patients")
        total_patients = db.execute(total_query).scalar()
        
        # Get gender distribution
        gender_query = text("""
            SELECT gender, COUNT(*) as count 
            FROM patients 
            GROUP BY gender
        """)
        gender_distribution = db.execute(gender_query).fetchall()
        
        # Get age groups
        age_query = text("""
            SELECT 
                CASE 
                    WHEN age < 18 THEN 'Child (0-17)'
                    WHEN age BETWEEN 18 AND 35 THEN 'Adult (18-35)'
                    WHEN age BETWEEN 36 AND 60 THEN 'Middle Age (36-60)'
                    ELSE 'Senior (60+)'
                END as age_group,
                COUNT(*) as count
            FROM patients
            GROUP BY age_group
            ORDER BY age_group
        """)
        age_distribution = db.execute(age_query).fetchall()
        
        # Recent registrations (last 30 days)
        recent_query = text("""
            SELECT COUNT(*) 
            FROM patients 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        recent_registrations = db.execute(recent_query).scalar()
        
        return {
            "success": True,
            "statistics": {
                "total_patients": total_patients,
                "recent_registrations": recent_registrations,
                "gender_distribution": [
                    {"gender": row.gender, "count": row.count} 
                    for row in gender_distribution
                ],
                "age_distribution": [
                    {"age_group": row.age_group, "count": row.count}
                    for row in age_distribution
                ]
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get patients statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# ===== HELPER FUNCTIONS =====

async def _save_patient_medications(
    db: Session, 
    no_rm: str, 
    medications: List[MedicationData], 
    medical_record_id: int
):
    """Helper function to save individual medications"""
    try:
        for med in medications:
            insert_medication_query = text("""
                INSERT INTO patient_medications (
                    no_rm, medication_name, dosage, frequency,
                    medical_record_id, notes, status,
                    start_date, created_at, updated_at
                ) VALUES (
                    :no_rm, :medication_name, :dosage, :frequency,
                    :medical_record_id, :notes, 'ACTIVE',
                    NOW(), NOW(), NOW()
                )
                ON DUPLICATE KEY UPDATE
                    dosage = VALUES(dosage),
                    frequency = VALUES(frequency),
                    notes = VALUES(notes),
                    updated_at = NOW()
            """)
            
            db.execute(insert_medication_query, {
                "no_rm": no_rm,
                "medication_name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "medical_record_id": medical_record_id,
                "notes": med.notes
            })
        
        db.commit()
        logger.info(f"✅ Successfully saved {len(medications)} medications for patient {no_rm}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save medications for {no_rm}: {e}")
        db.rollback()
        raise

def _format_patient_response(patient_row) -> Dict[str, Any]:
    """Helper function to format patient data consistently"""
    return {
        "no_rm": patient_row.no_rm,
        "name": patient_row.name,
        "age": patient_row.age,
        "gender": patient_row.gender,
        "phone": patient_row.phone,
        "address": patient_row.address,
        "weight_kg": patient_row.weight_kg,
        "height_cm": patient_row.height_cm,
        "blood_type": patient_row.blood_type,
        "allergies": patient_row.allergies,
        "created_at": patient_row.created_at.isoformat() if hasattr(patient_row, 'created_at') and patient_row.created_at else None,
        "updated_at": patient_row.updated_at.isoformat() if hasattr(patient_row, 'updated_at') and patient_row.updated_at else None
    }

def _build_search_condition(search_term: str) -> str:
    """Helper function to build search conditions"""
    return """
        WHERE (
            LOWER(name) LIKE :search_term OR 
            LOWER(no_rm) LIKE :search_term OR 
            LOWER(phone) LIKE :search_term OR
            LOWER(address) LIKE :search_term OR
            LOWER(blood_type) LIKE :search_term
        )
    """

# ===== ADVANCED ENDPOINTS =====

@router.get("/export")
async def export_patients(
    format: str = Query("json", pattern="^(json|csv)$", description="Export format"),
    db: Session = Depends(get_db)
):
    """Export patients data in JSON or CSV format"""
    try:
        patients_query = text("""
            SELECT no_rm, name, age, gender, phone, address, 
                   weight_kg, height_cm, blood_type, allergies,
                   created_at, updated_at
            FROM patients 
            ORDER BY name
        """)
        
        patients_result = db.execute(patients_query).fetchall()
        
        if format == "json":
            patients_list = []
            for patient in patients_result:
                patients_list.append(_format_patient_response(patient))
            
            return {
                "success": True,
                "format": "json",
                "data": patients_list,
                "total": len(patients_list),
                "exported_at": datetime.now().isoformat()
            }
        
        elif format == "csv":
            # For CSV format, we would typically return a file download
            # For now, return CSV-like structure
            csv_data = []
            headers = ["no_rm", "name", "age", "gender", "phone", "address", 
                      "weight_kg", "height_cm", "blood_type", "allergies"]
            csv_data.append(headers)
            
            for patient in patients_result:
                row = [
                    patient.no_rm or "",
                    patient.name or "",
                    str(patient.age) if patient.age else "",
                    patient.gender or "",
                    patient.phone or "",
                    patient.address or "",
                    str(patient.weight_kg) if patient.weight_kg else "",
                    str(patient.height_cm) if patient.height_cm else "",
                    patient.blood_type or "",
                    patient.allergies or ""
                ]
                csv_data.append(row)
            
            return {
                "success": True,
                "format": "csv",
                "data": csv_data,
                "total": len(csv_data) - 1,  # Excluding header
                "exported_at": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Failed to export patients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export patients: {str(e)}")

@router.get("/search-advanced")
async def search_patients_advanced(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    name: Optional[str] = Query(None, description="Search by name"),
    age_min: Optional[int] = Query(None, ge=0, description="Minimum age"),
    age_max: Optional[int] = Query(None, le=150, description="Maximum age"),
    gender: Optional[str] = Query(None, pattern="^(male|female)$", description="Gender filter"),
    blood_type: Optional[str] = Query(None, description="Blood type filter"),
    db: Session = Depends(get_db)
):
    """Advanced search with multiple filters"""
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Build dynamic query
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if name:
            conditions.append("LOWER(name) LIKE :name")
            params["name"] = f"%{name.lower()}%"
            
        if age_min is not None:
            conditions.append("age >= :age_min")
            params["age_min"] = age_min
            
        if age_max is not None:
            conditions.append("age <= :age_max")
            params["age_max"] = age_max
            
        if gender:
            conditions.append("gender = :gender")
            params["gender"] = gender
            
        if blood_type:
            conditions.append("LOWER(blood_type) = :blood_type")
            params["blood_type"] = blood_type.lower()
        
        # Build WHERE clause
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM patients {where_clause}"
        total_patients = db.execute(text(count_query), params).scalar()
        
        # Get patients
        patients_query = f"""
            SELECT no_rm, name, age, gender, phone, address, 
                   weight_kg, height_cm, blood_type, allergies,
                   created_at, updated_at
            FROM patients 
            {where_clause}
            ORDER BY name 
            LIMIT :limit OFFSET :offset
        """
        
        patients_result = db.execute(text(patients_query), params).fetchall()
        
        # Format response
        patients_list = []
        for patient in patients_result:
            patients_list.append(_format_patient_response(patient))
        
        return {
            "patients": patients_list,
            "total": total_patients,
            "page": page,
            "limit": limit,
            "total_pages": (total_patients + limit - 1) // limit,
            "filters_applied": {
                "name": name,
                "age_range": f"{age_min}-{age_max}" if age_min or age_max else None,
                "gender": gender,
                "blood_type": blood_type
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed advanced search: {e}")
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

@router.post("/bulk-import")
async def bulk_import_patients(
    patients_data: List[PatientCreate],
    db: Session = Depends(get_db)
):
    """Bulk import multiple patients"""
    try:
        successful_imports = []
        failed_imports = []
        
        for patient_data in patients_data:
            try:
                # Check if patient already exists
                check_query = text("SELECT no_rm FROM patients WHERE no_rm = :no_rm")
                existing = db.execute(check_query, {"no_rm": patient_data.no_rm}).fetchone()
                
                if existing:
                    failed_imports.append({
                        "no_rm": patient_data.no_rm,
                        "name": patient_data.name,
                        "error": "Patient already exists"
                    })
                    continue
                
                # Insert patient
                insert_query = text("""
                    INSERT INTO patients (
                        no_rm, name, age, gender, phone, address,
                        weight_kg, height_cm, blood_type, allergies,
                        created_at, updated_at
                    ) VALUES (
                        :no_rm, :name, :age, :gender, :phone, :address,
                        :weight_kg, :height_cm, :blood_type, :allergies,
                        NOW(), NOW()
                    )
                """)
                
                db.execute(insert_query, {
                    "no_rm": patient_data.no_rm,
                    "name": patient_data.name,
                    "age": patient_data.age,
                    "gender": patient_data.gender,
                    "phone": patient_data.phone,
                    "address": patient_data.address,
                    "weight_kg": patient_data.weight_kg,
                    "height_cm": patient_data.height_cm,
                    "blood_type": patient_data.blood_type,
                    "allergies": patient_data.allergies
                })
                
                successful_imports.append({
                    "no_rm": patient_data.no_rm,
                    "name": patient_data.name
                })
                
            except Exception as e:
                failed_imports.append({
                    "no_rm": patient_data.no_rm,
                    "name": patient_data.name,
                    "error": str(e)
                })
        
        db.commit()
        
        return {
            "success": True,
            "summary": {
                "total_processed": len(patients_data),
                "successful_imports": len(successful_imports),
                "failed_imports": len(failed_imports)
            },
            "successful_imports": successful_imports,
            "failed_imports": failed_imports
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Bulk import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")

# ===== HEALTH CHECK ENDPOINT =====

@router.get("/health")
async def patients_health_check(db: Session = Depends(get_db)):
    """Health check for patients module"""
    try:
        # Test database connection
        test_query = text("SELECT COUNT(*) FROM patients LIMIT 1")
        db.execute(test_query).scalar()
        
        return {
            "status": "healthy",
            "module": "patients",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Patients health check failed: {e}")
        return {
            "status": "unhealthy",
            "module": "patients",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
