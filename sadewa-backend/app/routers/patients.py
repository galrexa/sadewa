# app/routers/patients_optimized.py
"""
OPTIMIZED Patient Management API for SADEWA
Priority: Registrasi Pasien + Fast Search + Validation
"""

import time
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel, Field, field_validator

from app.database import get_db
from app.models import Patient, MedicalRecord, PatientMedication, PatientDiagnosis, PatientAllergy
import logging

# Setup logging
logger = logging.getLogger(__name__)
router = APIRouter()

# ===== PYDANTIC SCHEMAS =====

class PatientRegistration(BaseModel):
    """Schema untuk registrasi pasien baru - OPTIMIZED"""
    name: str = Field(..., min_length=2, max_length=100, description="Nama lengkap pasien")
    age: int = Field(..., ge=0, le=150, description="Umur pasien")
    # DIGANTI: 'regex' diubah menjadi 'pattern' untuk Pydantic v2
    gender: str = Field(..., pattern="^(male|female)$", description="Jenis kelamin: male/female")
    # DIGANTI: 'regex' diubah menjadi 'pattern' untuk Pydantic v2
    phone: Optional[str] = Field(None, pattern="^[0-9+\\-\\s]{10,20}$", description="Nomor telepon")
    weight_kg: Optional[int] = Field(None, ge=1, le=500, description="Berat badan (kg)")
    
    # Additional fields untuk AI profiling
    medical_history: Optional[List[str]] = Field(default=[], description="Riwayat penyakit")
    risk_factors: Optional[List[str]] = Field(default=[], description="Faktor risiko")
    allergies: Optional[List[str]] = Field(default=[], description="Riwayat alergi")
    
    # DIGANTI: '@validator' diubah menjadi '@field_validator' untuk Pydantic v2
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Nama tidak boleh kosong')
        # Remove multiple spaces and titlecase
        return ' '.join(v.split()).title()
    
    # DIGANTI: '@validator' diubah menjadi '@field_validator' untuk Pydantic v2
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v:
            # Remove spaces and dashes, keep only numbers and +
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 10:
                raise ValueError('Nomor telepon terlalu pendek')
        return v
    
class PatientUpdate(BaseModel):
    """Schema untuk update data pasien"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    # DIGANTI: 'regex' diubah menjadi 'pattern' untuk Pydantic v2
    gender: Optional[str] = Field(None, pattern="^(male|female)$")
    # DIGANTI: 'regex' diubah menjadi 'pattern' untuk Pydantic v2
    phone: Optional[str] = Field(None, pattern="^[0-9+\\-\\s]{10,20}$")
    weight_kg: Optional[int] = Field(None, ge=1, le=500)

class PatientResponse(BaseModel):
    """Schema response pasien"""
    id: int
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    weight_kg: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    patient_code: str
    age_category: str
    bmi_category: Optional[str] = None
    
    class Config:
        from_attributes = True

class PatientSearchResult(BaseModel):
    """Schema untuk hasil pencarian pasien"""
    patients: List[PatientResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    search_query: Optional[str] = None
    processing_time_ms: float

# ===== UTILITY FUNCTIONS =====

def calculate_age_category(age: int) -> str:
    """Kategorisasi umur untuk AI analysis"""
    if age < 18:
        return "child"
    elif age < 65:
        return "adult"
    else:
        return "elderly"

def calculate_bmi_category(weight_kg: Optional[int], age: int) -> Optional[str]:
    """Estimasi kategori BMI (simplified)"""
    if not weight_kg or age < 18:
        return None
    
    # Simplified BMI calculation (assume average height)
    avg_height_m = 1.65  # Average Indonesian height
    bmi = weight_kg / (avg_height_m ** 2)
    
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25:
        return "normal"
    elif bmi < 30:
        return "overweight"
    else:
        return "obese"

def format_patient_response(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    patient_data['patient_code'] = patient_data['no_rm']
    patient_data['age_category'] = calculate_age_category(patient_data['age'])
    return patient_data

def generate_no_rm(patient_id: int) -> str:
    return f"rm{patient_id:04d}"

async def create_patient_timeline_entry(
    patient_id: int, 
    event_type: str, 
    event_data: Dict[str, Any],
    db: Session
):
    """Background task untuk mencatat timeline pasien"""
    try:
        timeline_query = text("""
            INSERT INTO patient_timeline (patient_id, event_type, event_date, event_data)
            VALUES (:patient_id, :event_type, NOW(), :event_data)
        """)
        
        db.execute(timeline_query, {
            "patient_id": patient_id,
            "event_type": event_type,
            "event_data": str(event_data)  # Convert to JSON string
        })
        db.commit()
        logger.info(f"Timeline entry created for patient {patient_id}: {event_type}")
        
    except Exception as e:
        logger.error(f"Failed to create timeline entry: {e}")
        db.rollback()

# ===== API ENDPOINTS =====

@router.post("/patients/register", response_model=PatientResponse, status_code=201)
async def register_patient(patient_data: PatientRegistration, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """OPTIMIZED Patient Registration Endpoint"""
    start_time = time.time()
    try:
        if patient_data.phone:
            duplicate_check = text("SELECT id, name FROM patients WHERE name = :name AND phone = :phone LIMIT 1")
            duplicate = db.execute(duplicate_check, {"name": patient_data.name, "phone": patient_data.phone}).fetchone()
            if duplicate:
                raise HTTPException(status_code=409, detail=f"Pasien dengan nama '{duplicate.name}' dan nomor telepon yang sama sudah terdaftar (ID: {duplicate.id})")
        
        insert_query = text("INSERT INTO patients (name, age, gender, phone, weight_kg, created_at, updated_at) VALUES (:name, :age, :gender, :phone, :weight_kg, NOW(), NOW())")
        result = db.execute(insert_query, patient_data.model_dump(include={'name', 'age', 'gender', 'phone', 'weight_kg'}))
        new_patient_id = result.lastrowid
        
        if patient_data.allergies:
            for allergen in patient_data.allergies:
                allergy_query = text("INSERT INTO patient_allergies (patient_id, allergen, reaction_type) VALUES (:patient_id, :allergen, 'unknown')")
                db.execute(allergy_query, {"patient_id": new_patient_id, "allergen": allergen})
        
        db.commit()
        patient = db.execute(text("SELECT * FROM patients WHERE id = :patient_id"), {"patient_id": new_patient_id}).fetchone()
        patient_dict = dict(patient._mapping)
        formatted_patient = format_patient_response(patient_dict)
        
        background_tasks.add_task(create_patient_timeline_entry, new_patient_id, "registration", {"action": "patient_registered"}, db)
        
        return PatientResponse(**formatted_patient)
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        raise HTTPException(status_code=409, detail="Data pasien sudah ada atau konflik database")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during registration: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal mendaftarkan pasien: {str(e)}")

@router.get("/patients/search", response_model=PatientSearchResult)
async def search_patients(
    # DIGANTI: 'regex' diubah menjadi 'pattern' untuk Pydantic v2
    gender: Optional[str] = Query(None, pattern="^(male|female)$", description="Filter jenis kelamin"),
    q: Optional[str] = Query(None, description="Search query (nama, ID, telepon)"),
    age_min: Optional[int] = Query(None, ge=0, le=150, description="Umur minimum"),
    age_max: Optional[int] = Query(None, ge=0, le=150, description="Umur maksimum"),
    page: int = Query(1, ge=1, description="Halaman"),
    limit: int = Query(20, ge=1, le=100, description="Jumlah per halaman"),
    db: Session = Depends(get_db)
):
    """OPTIMIZED Patient Search dengan multiple filters"""
    start_time = time.time()
    try:
        where_conditions, params = ["1=1"], {}
        if q:
            if q.startswith('P') and q[1:].isdigit():
                where_conditions.append("id = :patient_id")
                params["patient_id"] = int(q[1:])
            elif q.isdigit():
                where_conditions.append("(id = :search_id OR phone LIKE :phone_pattern)")
                params.update({"search_id": int(q), "phone_pattern": f"%{q}%"})
            else:
                where_conditions.append("name LIKE :name_pattern")
                params["name_pattern"] = f"%{q}%"
        if gender:
            where_conditions.append("gender = :gender")
            params["gender"] = gender
        if age_min is not None:
            where_conditions.append("age >= :age_min")
            params["age_min"] = age_min
        if age_max is not None:
            where_conditions.append("age <= :age_max")
            params["age_max"] = age_max
        
        where_clause = " AND ".join(where_conditions)
        count_query = text(f"SELECT COUNT(*) FROM patients WHERE {where_clause}")
        total = db.execute(count_query, params).scalar()
        
        offset = (page - 1) * limit
        total_pages = (total + limit - 1) // limit
        
        search_query = text(f"SELECT * FROM patients WHERE {where_clause} ORDER BY created_at DESC LIMIT :limit OFFSET :offset")
        params.update({"limit": limit, "offset": offset})
        patients = db.execute(search_query, params).fetchall()
        formatted_patients = [PatientResponse(**format_patient_response(dict(p._mapping))) for p in patients]
        
        return PatientSearchResult(
            patients=formatted_patients,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            search_query=q,
            processing_time_ms=(time.time() - start_time) * 1000
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error during search: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal mencari pasien: {str(e)}")
    
@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient_detail(
    patient_id: int,
    include_timeline: bool = Query(False, description="Include patient timeline"),
    db: Session = Depends(get_db)
):
    """
    Get patient detail dengan optimasi
    - Support patient code (P0001) atau ID langsung
    - Optional timeline inclusion
    - Fast lookup dengan index
    """
    try:
        # Parse patient ID
        if patient_id.startswith('P'):
            numeric_id = int(patient_id[1:])
        else:
            numeric_id = int(patient_id)
        
        # Get patient data
        patient_query = text("SELECT * FROM patients WHERE id = :patient_id")
        patient = db.execute(patient_query, {"patient_id": numeric_id}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        # Format response
        patient_dict = dict(patient._mapping)
        formatted_patient = format_patient_response(patient_dict)
        
        response_data = PatientResponse(**formatted_patient)
        
        # Add timeline if requested
        if include_timeline:
            timeline_query = text("""
                SELECT event_type, event_date, event_data 
                FROM patient_timeline 
                WHERE patient_id = :patient_id 
                ORDER BY event_date DESC 
                LIMIT 10
            """)
            timeline = db.execute(timeline_query, {"patient_id": numeric_id}).fetchall()
            
            # Add timeline to response (extend the model if needed)
            response_data.timeline = [dict(t._mapping) for t in timeline]
        
        return response_data
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Format ID pasien tidak valid")
    except SQLAlchemyError as e:
        logger.error(f"Database error getting patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil data pasien")

@router.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    update_data: PatientUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Update patient data dengan audit trail
    """
    try:
        # Parse patient ID
        if patient_id.startswith('P'):
            numeric_id = int(patient_id[1:])
        else:
            numeric_id = int(patient_id)
        
        # Check if patient exists
        existing = db.execute(
            text("SELECT * FROM patients WHERE id = :patient_id"),
            {"patient_id": numeric_id}
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        # Build update query
        update_fields = []
        params = {"patient_id": numeric_id}
        
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                params[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="Tidak ada data yang diubah")
        
        # Execute update
        update_query = text(f"""
            UPDATE patients 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = :patient_id
        """)
        
        db.execute(update_query, params)
        db.commit()
        
        # Get updated data
        updated_patient = db.execute(
            text("SELECT * FROM patients WHERE id = :patient_id"),
            {"patient_id": numeric_id}
        ).fetchone()
        
        # Format response
        patient_dict = dict(updated_patient._mapping)
        formatted_patient = format_patient_response(patient_dict)
        
        # Background task for timeline
        background_tasks.add_task(
            create_patient_timeline_entry,
            numeric_id,
            "update",
            {"action": "patient_updated", "changes": update_data.dict(exclude_unset=True)},
            db
        )
        
        return PatientResponse(**formatted_patient)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Format ID pasien tidak valid")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengupdate data pasien")

@router.post("/patients/{patient_id}/save-diagnosis")
async def save_patient_diagnosis(
    patient_id: str,
    diagnosis_data: dict,
    db: Session = Depends(get_db)
):
    try:
        print(f"DEBUG - Received request for patient {patient_id}")
        
        # Validate patient exists
        patient = db.query(Patient).filter(Patient.no_rm == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Extract medications properly
        medications_data = diagnosis_data.get('medications', [])
        
        # Process medications: extract only essential fields
        processed_medications = []
        for med in medications_data:
            if isinstance(med, dict):
                processed_medications.append({
                    "name": med.get('name', ''),
                    "dosage": med.get('dosage', ''),
                    "frequency": med.get('frequency', ''),
                    "notes": med.get('notes', '')
                })
            else:
                # If medication is string, keep as is
                processed_medications.append(str(med))
        
        # Create medical record with proper JSON structure
        new_record = MedicalRecord(
            no_rm=patient_id,
            diagnosis_code=diagnosis_data.get('diagnosis_code'),
            diagnosis_text=diagnosis_data.get('diagnosis_text'),
            medications=processed_medications,  # Let SQLAlchemy handle JSON conversion
            interactions=diagnosis_data.get('interaction_results'),  # Store full interaction results
            notes=diagnosis_data.get('notes'),
        )
        
        db.add(new_record)
        db.commit()
        
        print(f"DEBUG - Successfully saved medical record")
        
        return {"success": True, "message": "Diagnosis saved successfully", "record_id": new_record.id}
        
    except Exception as e:
        print(f"ERROR - {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/patients/stats/summary")
async def get_patient_statistics(db: Session = Depends(get_db)):
    """
    Get patient statistics untuk dashboard
    """
    try:
        stats_query = text("""
            SELECT 
                COUNT(*) as total_patients,
                COUNT(CASE WHEN gender = 'male' THEN 1 END) as male_count,
                COUNT(CASE WHEN gender = 'female' THEN 1 END) as female_count,
                COUNT(CASE WHEN age < 18 THEN 1 END) as children_count,
                COUNT(CASE WHEN age >= 18 AND age < 65 THEN 1 END) as adult_count,
                COUNT(CASE WHEN age >= 65 THEN 1 END) as elderly_count,
                AVG(age) as average_age,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as new_this_week,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as new_this_month
            FROM patients
        """)
        
        stats = db.execute(stats_query).fetchone()
        
        return {
            "total_patients": stats.total_patients,
            "gender_distribution": {
                "male": stats.male_count,
                "female": stats.female_count
            },
            "age_distribution": {
                "children": stats.children_count,
                "adults": stats.adult_count,
                "elderly": stats.elderly_count
            },
            "average_age": round(float(stats.average_age), 1) if stats.average_age else 0,
            "registrations": {
                "this_week": stats.new_this_week,
                "this_month": stats.new_this_month
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting patient stats: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil statistik pasien")