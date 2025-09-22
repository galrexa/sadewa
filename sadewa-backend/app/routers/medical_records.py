# app/routers/medical_records_optimized.py
"""
OPTIMIZED Medical Records API for SADEWA
Priority: Anamnesis + Structured Data + Fast Retrieval
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

# ===== ENUMS =====

class SymptomSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

class SymptomDuration(str, Enum):
    ACUTE = "acute"  # < 1 week
    SUBACUTE = "subacute"  # 1-4 weeks
    CHRONIC = "chronic"  # > 4 weeks

class VisitType(str, Enum):
    INITIAL = "initial"
    FOLLOWUP = "followup"
    EMERGENCY = "emergency"
    CONSULTATION = "consultation"

# ===== PYDANTIC SCHEMAS =====

class SymptomData(BaseModel):
    """Schema untuk data gejala terstruktur"""
    symptom: str = Field(..., description="Nama gejala")
    severity: SymptomSeverity = Field(..., description="Tingkat keparahan")
    duration: SymptomDuration = Field(..., description="Durasi gejala")
    description: Optional[str] = Field(None, description="Deskripsi detail")
    onset_date: Optional[date] = Field(None, description="Tanggal mulai gejala")

class VitalSigns(BaseModel):
    """Schema untuk tanda vital"""
    blood_pressure_systolic: Optional[int] = Field(None, ge=50, le=300)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=30, le=200)
    heart_rate: Optional[int] = Field(None, ge=30, le=250, description="BPM")
    temperature: Optional[float] = Field(None, ge=30.0, le=45.0, description="Celsius")
    respiratory_rate: Optional[int] = Field(None, ge=8, le=60, description="Per minute")
    oxygen_saturation: Optional[int] = Field(None, ge=70, le=100, description="Percentage")
    weight_kg: Optional[float] = Field(None, ge=0.1, le=500.0)
    height_cm: Optional[float] = Field(None, ge=30.0, le=250.0)

class MedicalRecordCreate(BaseModel):
    """Schema untuk membuat medical record baru"""
    patient_id: int = Field(..., description="ID pasien")
    visit_type: VisitType = Field(default=VisitType.INITIAL, description="Jenis kunjungan")
    
    # Chief complaint & symptoms
    chief_complaint: str = Field(..., min_length=5, max_length=500, description="Keluhan utama")
    symptoms: List[SymptomData] = Field(default=[], description="Daftar gejala terstruktur")
    
    # Physical examination
    vital_signs: Optional[VitalSigns] = Field(None, description="Tanda vital")
    physical_examination: Optional[str] = Field(None, description="Hasil pemeriksaan fisik")
    
    # Diagnosis
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Diagnosis dalam teks")
    differential_diagnosis: Optional[List[str]] = Field(default=[], description="Diagnosis banding")
    
    # Treatment
    medications: Optional[List[str]] = Field(default=[], description="Daftar obat")
    treatment_plan: Optional[str] = Field(None, description="Rencana perawatan")
    
    # Notes
    notes: Optional[str] = Field(None, description="Catatan tambahan")
    follow_up_date: Optional[date] = Field(None, description="Tanggal kontrol")
    
    @validator('chief_complaint')
    def validate_chief_complaint(cls, v):
        return v.strip()

class MedicalRecordUpdate(BaseModel):
    """Schema untuk update medical record"""
    visit_type: Optional[VisitType] = None
    chief_complaint: Optional[str] = Field(None, min_length=5, max_length=500)
    symptoms: Optional[List[SymptomData]] = None
    vital_signs: Optional[VitalSigns] = None
    physical_examination: Optional[str] = None
    diagnosis_code: Optional[str] = None
    diagnosis_text: Optional[str] = None
    differential_diagnosis: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None

class MedicalRecordResponse(BaseModel):
    """Schema response medical record"""
    id: int
    patient_id: int
    visit_type: str
    chief_complaint: str
    symptoms: List[Dict[str, Any]]
    vital_signs: Optional[Dict[str, Any]] = None
    physical_examination: Optional[str] = None
    diagnosis_code: Optional[str] = None
    diagnosis_text: Optional[str] = None
    differential_diagnosis: List[str] = []
    medications: List[str] = []
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    patient_name: Optional[str] = None
    symptom_count: int = 0
    medication_count: int = 0
    risk_level: str = "low"  # low, medium, high

class PatientHistoryResponse(BaseModel):
    """Schema untuk riwayat medis pasien"""
    patient_id: int
    patient_name: str
    medical_records: List[MedicalRecordResponse]
    total_visits: int
    last_visit: Optional[datetime] = None
    chronic_conditions: List[str] = []
    current_medications: List[str] = []
    allergies: List[str] = []

# ===== UTILITY FUNCTIONS =====

def calculate_risk_level(symptoms: List[Dict], vital_signs: Optional[Dict]) -> str:
    """Calculate patient risk level based on symptoms and vitals"""
    risk_score = 0
    
    # Check severe symptoms
    severe_symptoms = [s for s in symptoms if s.get('severity') == 'severe']
    risk_score += len(severe_symptoms) * 2
    
    # Check vital signs
    if vital_signs:
        if vital_signs.get('temperature', 0) > 38.5:  # High fever
            risk_score += 2
        if vital_signs.get('heart_rate', 0) > 120:  # Tachycardia
            risk_score += 1
        if vital_signs.get('oxygen_saturation', 100) < 95:  # Low oxygen
            risk_score += 3
    
    if risk_score >= 5:
        return "high"
    elif risk_score >= 2:
        return "medium"
    else:
        return "low"

def format_medical_record_response(record_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format medical record dengan computed fields"""
    
    # Parse JSON fields
    symptoms = json.loads(record_data.get('symptoms', '[]')) if record_data.get('symptoms') else []
    medications = json.loads(record_data.get('medications', '[]')) if record_data.get('medications') else []
    differential_diagnosis = json.loads(record_data.get('differential_diagnosis', '[]')) if record_data.get('differential_diagnosis') else []
    vital_signs = json.loads(record_data.get('vital_signs', '{}')) if record_data.get('vital_signs') else {}
    
    # Calculate computed fields
    record_data['symptoms'] = symptoms
    record_data['medications'] = medications
    record_data['differential_diagnosis'] = differential_diagnosis
    record_data['vital_signs'] = vital_signs if vital_signs else None
    record_data['symptom_count'] = len(symptoms)
    record_data['medication_count'] = len(medications)
    record_data['risk_level'] = calculate_risk_level(symptoms, vital_signs)
    
    return record_data

async def create_medical_timeline_entry(
    patient_id: int,
    medical_record_id: int,
    event_type: str,
    event_data: Dict[str, Any],
    db: Session
):
    """Background task untuk timeline medis"""
    try:
        timeline_query = text("""
            INSERT INTO patient_timeline (patient_id, event_type, event_date, event_data, medical_record_id)
            VALUES (:patient_id, :event_type, NOW(), :event_data, :medical_record_id)
        """)
        
        db.execute(timeline_query, {
            "patient_id": patient_id,
            "event_type": event_type,
            "event_data": json.dumps(event_data),
            "medical_record_id": medical_record_id
        })
        db.commit()
        logger.info(f"Medical timeline entry created for patient {patient_id}: {event_type}")
        
    except Exception as e:
        logger.error(f"Failed to create medical timeline entry: {e}")
        db.rollback()

# ===== API ENDPOINTS =====

@router.post("/medical-records", response_model=MedicalRecordResponse, status_code=201)
async def create_medical_record(
    record_data: MedicalRecordCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED Create Medical Record (Anamnesis)
    - Structured symptom data
    - Vital signs tracking
    - Risk level calculation
    - Auto timeline creation
    """
    start_time = time.time()
    
    try:
        # 1. Validate patient exists
        patient_check = text("SELECT id, name FROM patients WHERE id = :patient_id")
        patient = db.execute(patient_check, {"patient_id": record_data.patient_id}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        # 2. Prepare data for insertion
        symptoms_json = json.dumps([symptom.dict() for symptom in record_data.symptoms])
        vital_signs_json = json.dumps(record_data.vital_signs.dict()) if record_data.vital_signs else None
        medications_json = json.dumps(record_data.medications)
        differential_json = json.dumps(record_data.differential_diagnosis)
        
        # 3. Insert medical record
        insert_query = text("""
            INSERT INTO medical_records (
                patient_id, diagnosis_code, diagnosis_text, medications, notes,
                symptoms, interactions, created_at, updated_at
            ) VALUES (
                :patient_id, :diagnosis_code, :diagnosis_text, :medications, :notes,
                :symptoms, :interactions, NOW(), NOW()
            )
        """)
        
        # Prepare comprehensive notes
        comprehensive_notes = []
        if record_data.chief_complaint:
            comprehensive_notes.append(f"Keluhan Utama: {record_data.chief_complaint}")
        if record_data.physical_examination:
            comprehensive_notes.append(f"Pemeriksaan Fisik: {record_data.physical_examination}")
        if record_data.treatment_plan:
            comprehensive_notes.append(f"Rencana Perawatan: {record_data.treatment_plan}")
        if record_data.notes:
            comprehensive_notes.append(f"Catatan: {record_data.notes}")
        if record_data.follow_up_date:
            comprehensive_notes.append(f"Kontrol: {record_data.follow_up_date}")
        
        notes_text = "\n\n".join(comprehensive_notes)
        
        # Prepare interactions data
        interactions_data = {
            "visit_type": record_data.visit_type,
            "chief_complaint": record_data.chief_complaint,
            "vital_signs": record_data.vital_signs.dict() if record_data.vital_signs else None,
            "differential_diagnosis": record_data.differential_diagnosis,
            "treatment_plan": record_data.treatment_plan,
            "follow_up_date": record_data.follow_up_date.isoformat() if record_data.follow_up_date else None
        }
        
        result = db.execute(insert_query, {
            "patient_id": record_data.patient_id,
            "diagnosis_code": record_data.diagnosis_code,
            "diagnosis_text": record_data.diagnosis_text,
            "medications": medications_json,
            "notes": notes_text,
            "symptoms": symptoms_json,
            "interactions": json.dumps(interactions_data)
        })
        
        new_record_id = result.lastrowid
        db.commit()
        
        # 4. Get complete record data
        record_query = text("""
            SELECT mr.*, p.name as patient_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            WHERE mr.id = :record_id
        """)
        record = db.execute(record_query, {"record_id": new_record_id}).fetchone()
        
        # 5. Format response
        record_dict = dict(record._mapping)
        formatted_record = format_medical_record_response(record_dict)
        
        # 6. Background task untuk timeline
        background_tasks.add_task(
            create_medical_timeline_entry,
            record_data.patient_id,
            new_record_id,
            "visit",
            {
                "action": "medical_record_created",
                "visit_type": record_data.visit_type,
                "chief_complaint": record_data.chief_complaint,
                "symptom_count": len(record_data.symptoms),
                "medication_count": len(record_data.medications),
                "processing_time_ms": (time.time() - start_time) * 1000
            },
            db
        )
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Medical record {new_record_id} created successfully in {processing_time:.2f}ms")
        
        return MedicalRecordResponse(**formatted_record)
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating medical record: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal membuat rekam medis: {str(e)}")

@router.get("/medical-records/patient/{patient_id}", response_model=PatientHistoryResponse)
async def get_patient_medical_history(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50, description="Jumlah record terakhir"),
    include_allergies: bool = Query(True, description="Include allergy information"),
    db: Session = Depends(get_db)
):
    """
    Get complete patient medical history dengan optimasi
    - Paginated medical records
    - Include allergies and current medications
    - Chronic conditions detection
    """
    try:
        # 1. Get patient info
        patient_query = text("SELECT id, name FROM patients WHERE id = :patient_id")
        patient = db.execute(patient_query, {"patient_id": patient_id}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        # 2. Get medical records
        records_query = text("""
            SELECT mr.*, p.name as patient_name
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
        
        # 3. Format medical records
        formatted_records = []
        for record in records:
            record_dict = dict(record._mapping)
            formatted_record = format_medical_record_response(record_dict)
            formatted_records.append(MedicalRecordResponse(**formatted_record))
        
        # 4. Get allergies if requested
        allergies = []
        if include_allergies:
            allergy_query = text("""
                SELECT allergen, reaction_type 
                FROM patient_allergies 
                WHERE patient_id = :patient_id
            """)
            allergy_results = db.execute(allergy_query, {"patient_id": patient_id}).fetchall()
            allergies = [f"{a.allergen} ({a.reaction_type})" if a.reaction_type else a.allergen 
                        for a in allergy_results]
        
        # 5. Get current medications
        current_medications = []
        if records:
            latest_record = records[0]
            medications_data = latest_record.medications
            if medications_data:
                try:
                    current_medications = json.loads(medications_data)
                except:
                    current_medications = []
        
        # 6. Detect chronic conditions (simplified)
        chronic_conditions = []
        diagnosis_frequency = {}
        for record in records:
            if record.diagnosis_text:
                diagnosis_frequency[record.diagnosis_text] = diagnosis_frequency.get(record.diagnosis_text, 0) + 1
        
        # Consider conditions appearing 3+ times as chronic
        chronic_conditions = [diagnosis for diagnosis, count in diagnosis_frequency.items() if count >= 3]
        
        # 7. Get statistics
        stats_query = text("""
            SELECT 
                COUNT(*) as total_visits,
                MAX(created_at) as last_visit
            FROM medical_records 
            WHERE patient_id = :patient_id
        """)
        stats = db.execute(stats_query, {"patient_id": patient_id}).fetchone()
        
        return PatientHistoryResponse(
            patient_id=patient_id,
            patient_name=patient.name,
            medical_records=formatted_records,
            total_visits=stats.total_visits,
            last_visit=stats.last_visit,
            chronic_conditions=chronic_conditions,
            current_medications=current_medications,
            allergies=allergies
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting patient history {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil riwayat medis pasien")

@router.get("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record_detail(
    record_id: int,
    db: Session = Depends(get_db)
):
    """Get detail medical record"""
    try:
        record_query = text("""
            SELECT mr.*, p.name as patient_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            WHERE mr.id = :record_id
        """)
        
        record = db.execute(record_query, {"record_id": record_id}).fetchone()
        
        if not record:
            raise HTTPException(status_code=404, detail="Rekam medis tidak ditemukan")
        
        # Format response
        record_dict = dict(record._mapping)
        formatted_record = format_medical_record_response(record_dict)
        
        return MedicalRecordResponse(**formatted_record)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting medical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil detail rekam medis")

@router.put("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    record_id: int,
    update_data: MedicalRecordUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update medical record dengan audit trail"""
    try:
        # Check if record exists
        existing_query = text("SELECT * FROM medical_records WHERE id = :record_id")
        existing = db.execute(existing_query, {"record_id": record_id}).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Rekam medis tidak ditemukan")
        
        # Build update query
        update_fields = []
        params = {"record_id": record_id}
        
        # Handle complex fields
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if value is not None:
                if field == 'symptoms':
                    update_fields.append("symptoms = :symptoms")
                    params["symptoms"] = json.dumps([symptom.dict() for symptom in value])
                elif field == 'vital_signs':
                    # Update interactions JSON with new vital signs
                    current_interactions = json.loads(existing.interactions or '{}')
                    current_interactions['vital_signs'] = value.dict()
                    update_fields.append("interactions = :interactions")
                    params["interactions"] = json.dumps(current_interactions)
                elif field in ['medications', 'differential_diagnosis']:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = json.dumps(value)
                else:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="Tidak ada data yang diubah")
        
        # Execute update
        update_query = text(f"""
            UPDATE medical_records 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = :record_id
        """)
        
        db.execute(update_query, params)
        db.commit()
        
        # Get updated data
        updated_record = db.execute(
            text("""
                SELECT mr.*, p.name as patient_name
                FROM medical_records mr
                JOIN patients p ON mr.patient_id = p.id
                WHERE mr.id = :record_id
            """),
            {"record_id": record_id}
        ).fetchone()
        
        # Format response
        record_dict = dict(updated_record._mapping)
        formatted_record = format_medical_record_response(record_dict)
        
        # Background task for timeline
        background_tasks.add_task(
            create_medical_timeline_entry,
            existing.patient_id,
            record_id,
            "update",
            {"action": "medical_record_updated", "changes": update_dict},
            db
        )
        
        return MedicalRecordResponse(**formatted_record)
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating medical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengupdate rekam medis")

@router.get("/medical-records/search/symptoms")
async def search_by_symptoms(
    symptoms: str = Query(..., description="Comma-separated symptoms"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search medical records by symptoms
    Useful untuk pattern recognition dan AI training
    """
    try:
        symptom_list = [s.strip().lower() for s in symptoms.split(',')]
        
        # Search in symptoms JSON and notes
        search_conditions = []
        params = {"limit": limit}
        
        for i, symptom in enumerate(symptom_list):
            param_name = f"symptom_{i}"
            search_conditions.append(f"(LOWER(symptoms) LIKE :{param_name} OR LOWER(notes) LIKE :{param_name})")
            params[param_name] = f"%{symptom}%"
        
        where_clause = " OR ".join(search_conditions)
        
        search_query = text(f"""
            SELECT mr.*, p.name as patient_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            WHERE {where_clause}
            ORDER BY mr.created_at DESC
            LIMIT :limit
        """)
        
        records = db.execute(search_query, params).fetchall()
        
        # Format results
        formatted_records = []
        for record in records:
            record_dict = dict(record._mapping)
            formatted_record = format_medical_record_response(record_dict)
            formatted_records.append(MedicalRecordResponse(**formatted_record))
        
        return {
            "search_terms": symptom_list,
            "total_found": len(formatted_records),
            "medical_records": formatted_records
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error searching symptoms: {e}")
        raise HTTPException(status_code=500, detail="Gagal mencari berdasarkan gejala")

@router.get("/medical-records/stats/summary")
async def get_medical_records_statistics(
    days: int = Query(30, ge=1, le=365, description="Periode hari"),
    db: Session = Depends(get_db)
):
    """Get medical records statistics untuk dashboard"""
    try:
        stats_query = text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT patient_id) as unique_patients,
                COUNT(CASE WHEN diagnosis_code IS NOT NULL THEN 1 END) as records_with_diagnosis,
                COUNT(CASE WHEN JSON_LENGTH(medications) > 0 THEN 1 END) as records_with_medications,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL :days DAY) THEN 1 END) as recent_records,
                AVG(JSON_LENGTH(medications)) as avg_medications_per_record
            FROM medical_records
        """)
        
        stats = db.execute(stats_query, {"days": days}).fetchone()
        
        # Get most common diagnoses
        diagnosis_query = text("""
            SELECT diagnosis_text, COUNT(*) as count
            FROM medical_records 
            WHERE diagnosis_text IS NOT NULL 
            AND created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY diagnosis_text
            ORDER BY count DESC
            LIMIT 10
        """)
        
        common_diagnoses = db.execute(diagnosis_query, {"days": days}).fetchall()
        
        return {
            "period_days": days,
            "total_records": stats.total_records,
            "unique_patients": stats.unique_patients,
            "records_with_diagnosis": stats.records_with_diagnosis,
            "records_with_medications": stats.records_with_medications,
            "recent_records": stats.recent_records,
            "avg_medications_per_record": round(float(stats.avg_medications_per_record or 0), 1),
            "common_diagnoses": [
                {"diagnosis": d.diagnosis_text, "count": d.count} 
                for d in common_diagnoses
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting medical records stats: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil statistik rekam medis")