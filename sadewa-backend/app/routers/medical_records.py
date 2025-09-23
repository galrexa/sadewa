# app/routers/medical_records_optimized.py
"""
OPTIMIZED Medical Records API for SADEWA
Priority: Anamnesis + Structured Data + Fast Retrieval
FIXED: Using patient_medications with no_rm
"""

import time
import json
from datetime import datetime, date, timedelta
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

class MedicationStatus(str, Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"

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

class MedicationData(BaseModel):
    """Schema untuk data obat"""
    name: str = Field(..., description="Nama obat")
    dosage: str = Field(..., description="Dosis obat")
    frequency: str = Field(..., description="Frekuensi minum")
    duration: Optional[str] = Field(None, description="Durasi pengobatan")
    notes: Optional[str] = Field(None, description="Catatan obat")

class CurrentMedication(BaseModel):
    """Schema untuk current medication response"""
    id: int
    name: str
    dosage: Optional[str]
    frequency: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    prescribed_by: Optional[str]

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
    
    # Treatment - ✅ FIXED: Using MedicationData
    medications: Optional[List[MedicationData]] = Field(default=[], description="Daftar obat terstruktur")
    treatment_plan: Optional[str] = Field(None, description="Rencana perawatan")
    
    # Notes
    notes: Optional[str] = Field(None, description="Catatan tambahan")
    follow_up_date: Optional[date] = Field(None, description="Tanggal kontrol")
    prescribed_by: Optional[str] = Field(None, description="Nama dokter")
    
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
    medications: Optional[List[MedicationData]] = None
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
    medications: List[Dict[str, Any]] = []  # ✅ FIXED: Dict untuk structured data
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
    current_medications: List[CurrentMedication] = []  # ✅ FIXED: Structured medications
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

# ✅ NEW: Medication management functions
async def add_medications_to_patient(
    no_rm: str,
    medications: List[MedicationData],
    prescribed_by: str,
    medical_record_id: int,
    db: Session
):
    """Add medications to patient_medications table"""
    try:
        for med in medications:
            # Calculate end date if duration provided
            end_date = None
            if med.duration:
                # Simple duration parsing (e.g., "7 hari", "2 minggu")
                try:
                    if "hari" in med.duration.lower():
                        days = int(med.duration.split()[0])
                        end_date = date.today() + timedelta(days=days)
                    elif "minggu" in med.duration.lower():
                        weeks = int(med.duration.split()[0])
                        end_date = date.today() + timedelta(weeks=weeks)
                except:
                    pass  # If parsing fails, leave end_date as None
            
            insert_query = text("""
                INSERT INTO patient_medications 
                (no_rm, medication_name, dosage, frequency, start_date, end_date, 
                 status, prescribed_by, medical_record_id, is_active)
                VALUES (:no_rm, :medication_name, :dosage, :frequency, :start_date, :end_date,
                        :status, :prescribed_by, :medical_record_id, 1)
                ON DUPLICATE KEY UPDATE
                    dosage = VALUES(dosage),
                    frequency = VALUES(frequency),
                    end_date = VALUES(end_date),
                    status = 'active',
                    is_active = 1,
                    medical_record_id = VALUES(medical_record_id)
            """)
            
            db.execute(insert_query, {
                "no_rm": no_rm,
                "medication_name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "start_date": date.today(),
                "end_date": end_date,
                "status": "active",
                "prescribed_by": prescribed_by,
                "medical_record_id": medical_record_id
            })
        
        db.commit()
        logger.info(f"Added {len(medications)} medications for patient {no_rm}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add medications for patient {no_rm}: {e}")
        raise

async def get_current_medications(patient_id: int, db: Session) -> List[CurrentMedication]:
    """✅ FIXED: Get current medications from patient_medications table"""
    try:
        query = text("""
            SELECT 
                pm.id,
                pm.medication_name as name,
                pm.dosage,
                pm.frequency,
                pm.start_date,
                pm.end_date,
                pm.status,
                pm.prescribed_by
            FROM patient_medications pm
            JOIN patients p ON pm.no_rm = p.no_rm
            WHERE p.id = :patient_id
              AND pm.status = 'active'
              AND pm.is_active = 1
              AND (pm.end_date IS NULL OR pm.end_date > CURDATE())
            ORDER BY pm.start_date DESC
        """)
        
        results = db.execute(query, {"patient_id": patient_id}).fetchall()
        
        return [
            CurrentMedication(
                id=row.id,
                name=row.name,
                dosage=row.dosage,
                frequency=row.frequency,
                start_date=row.start_date,
                end_date=row.end_date,
                status=row.status,
                prescribed_by=row.prescribed_by
            )
            for row in results
        ]
        
    except Exception as e:
        logger.error(f"Error getting current medications for patient {patient_id}: {e}")
        return []

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
    ✅ FIXED: Create Medical Record with patient_medications integration
    """
    start_time = time.time()
    
    try:
        # 1. Validate patient exists and get no_rm
        patient_check = text("SELECT id, name, no_rm FROM patients WHERE id = :patient_id")
        patient = db.execute(patient_check, {"patient_id": record_data.patient_id}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        # 2. Prepare data for insertion
        symptoms_json = json.dumps([symptom.dict() for symptom in record_data.symptoms])
        vital_signs_json = json.dumps(record_data.vital_signs.dict()) if record_data.vital_signs else None
        medications_json = json.dumps([med.dict() for med in record_data.medications])  # ✅ Structured data
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
        
        # 4. ✅ NEW: Add medications to patient_medications table
        if record_data.medications:
            await add_medications_to_patient(
                no_rm=patient.no_rm,
                medications=record_data.medications,
                prescribed_by=record_data.prescribed_by or "Unknown",
                medical_record_id=new_record_id,
                db=db
            )
        
        # 5. Get complete record data
        record_query = text("""
            SELECT mr.*, p.name as patient_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            WHERE mr.id = :record_id
        """)
        record = db.execute(record_query, {"record_id": new_record_id}).fetchone()
        
        # 6. Format response
        record_dict = dict(record._mapping)
        formatted_record = format_medical_record_response(record_dict)
        
        # 7. Background task untuk timeline
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
    ✅ FIXED: Get complete patient medical history dengan current medications dari patient_medications
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
        
        # 5. ✅ FIXED: Get current medications from patient_medications table
        current_medications = await get_current_medications(patient_id, db)
        
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
            current_medications=current_medications,  # ✅ FIXED: Structured data
            allergies=allergies
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting patient history {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil riwayat medis pasien")

# ✅ NEW: Medication management endpoints
@router.get("/patients/{patient_id}/medications", response_model=List[CurrentMedication])
async def get_patient_current_medications(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Get current medications for a patient"""
    try:
        return await get_current_medications(patient_id, db)
    except Exception as e:
        logger.error(f"Error getting medications for patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil daftar obat pasien")

@router.post("/patients/{patient_id}/medications")
async def add_medication_to_patient(
    patient_id: int,
    medication: MedicationData,
    prescribed_by: str = Query(..., description="Nama dokter"),
    db: Session = Depends(get_db)
):
    """Add a single medication to patient"""
    try:
        # Get patient no_rm
        patient_query = text("SELECT no_rm FROM patients WHERE id = :patient_id")
        patient = db.execute(patient_query, {"patient_id": patient_id}).fetchone()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan")
        
        await add_medications_to_patient(
            no_rm=patient.no_rm,
            medications=[medication],
            prescribed_by=prescribed_by,
            medical_record_id=None,  # Not linked to specific record
            db=db
        )
        
        return {"message": "Obat berhasil ditambahkan", "medication": medication.name}
        
    except Exception as e:
        logger.error(f"Error adding medication to patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal menambahkan obat")

@router.put("/medications/{medication_id}/status")
async def update_medication_status(
    medication_id: int,
    status: MedicationStatus,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Update medication status (discontinue, complete, etc.)"""
    try:
        update_query = text("""
            UPDATE patient_medications 
            SET status = :status, 
                end_date = :end_date,
                is_active = CASE WHEN :status = 'active' THEN 1 ELSE 0 END
            WHERE id = :medication_id
        """)
        
        result = db.execute(update_query, {
            "medication_id": medication_id,
            "status": status.value,
            "end_date": end_date or date.today() if status != MedicationStatus.ACTIVE else None
        })
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Obat tidak ditemukan")
        
        db.commit()
        return {"message": f"Status obat berhasil diubah menjadi {status.value}"}
        
    except Exception as e:
        logger.error(f"Error updating medication status {medication_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengubah status obat")

# ===== EXISTING ENDPOINTS (keep as before) =====

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

@router.get("/medical-records/search/symptoms")
async def search_by_symptoms(
    symptoms: str = Query(..., description="Comma-separated symptoms"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search medical records by symptoms"""
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
        
        # ✅ NEW: Get medication statistics from patient_medications
        medication_stats_query = text("""
            SELECT 
                COUNT(*) as total_active_medications,
                COUNT(DISTINCT no_rm) as patients_with_medications,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_medications,
                COUNT(CASE WHEN status = 'discontinued' THEN 1 END) as discontinued_medications,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_medications
            FROM patient_medications
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
        """)
        
        med_stats = db.execute(medication_stats_query, {"days": days}).fetchone()
        
        return {
            "period_days": days,
            "medical_records": {
                "total_records": stats.total_records,
                "unique_patients": stats.unique_patients,
                "records_with_diagnosis": stats.records_with_diagnosis,
                "records_with_medications": stats.records_with_medications,
                "recent_records": stats.recent_records,
                "avg_medications_per_record": round(float(stats.avg_medications_per_record or 0), 1)
            },
            "medications": {
                "total_active_medications": med_stats.total_active_medications,
                "patients_with_medications": med_stats.patients_with_medications,
                "active_medications": med_stats.active_medications,
                "discontinued_medications": med_stats.discontinued_medications,
                "completed_medications": med_stats.completed_medications
            },
            "common_diagnoses": [
                {"diagnosis": d.diagnosis_text, "count": d.count} 
                for d in common_diagnoses
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting medical records stats: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil statistik rekam medis")

@router.put("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    record_id: int,
    update_data: MedicalRecordUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """✅ FIXED: Update medical record dengan medication sync"""
    try:
        # Check if record exists
        existing_query = text("SELECT * FROM medical_records WHERE id = :record_id")
        existing = db.execute(existing_query, {"record_id": record_id}).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Rekam medis tidak ditemukan")
        
        # Get patient info for medication updates
        patient_query = text("SELECT no_rm FROM patients WHERE id = :patient_id")
        patient = db.execute(patient_query, {"patient_id": existing.patient_id}).fetchone()
        
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
                elif field == 'medications':
                    # ✅ FIXED: Handle structured medication data
                    update_fields.append("medications = :medications")
                    params["medications"] = json.dumps([med.dict() for med in value])
                    
                    # ✅ NEW: Update patient_medications table
                    if patient and value:
                        # Mark existing medications as discontinued for this record
                        discontinue_query = text("""
                            UPDATE patient_medications 
                            SET status = 'discontinued', end_date = CURDATE()
                            WHERE medical_record_id = :record_id
                        """)
                        db.execute(discontinue_query, {"record_id": record_id})
                        
                        # Add new medications
                        await add_medications_to_patient(
                            no_rm=patient.no_rm,
                            medications=value,
                            prescribed_by="Updated",
                            medical_record_id=record_id,
                            db=db
                        )
                elif field == 'differential_diagnosis':
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

# ===== NEW MEDICATION ENDPOINTS =====

@router.get("/medications/search")
async def search_medications(
    query: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search medications in drugs database"""
    try:
        search_query = text("""
            SELECT id, nama_obat, nama_obat_internasional
            FROM drugs 
            WHERE is_active = 1 
            AND (LOWER(nama_obat) LIKE :query OR LOWER(nama_obat_internasional) LIKE :query)
            ORDER BY 
                CASE 
                    WHEN LOWER(nama_obat) LIKE :exact_query THEN 1
                    WHEN LOWER(nama_obat_internasional) LIKE :exact_query THEN 2
                    ELSE 3
                END,
                nama_obat
            LIMIT :limit
        """)
        
        results = db.execute(search_query, {
            "query": f"%{query.lower()}%",
            "exact_query": f"{query.lower()}%",
            "limit": limit
        }).fetchall()
        
        return [
            {
                "id": row.id,
                "nama_obat": row.nama_obat,
                "nama_obat_internasional": row.nama_obat_internasional,
                "display_name": f"{row.nama_obat} ({row.nama_obat_internasional})"
            }
            for row in results
        ]
        
    except Exception as e:
        logger.error(f"Error searching medications: {e}")
        raise HTTPException(status_code=500, detail="Gagal mencari obat")

@router.get("/medications/interactions/check")
async def check_medication_interactions(
    medications: str = Query(..., description="Comma-separated medication names"),
    db: Session = Depends(get_db)
):
    """Check drug interactions for multiple medications"""
    try:
        med_list = [med.strip() for med in medications.split(',') if med.strip()]
        
        if len(med_list) < 2:
            return {"interactions": [], "message": "Minimal 2 obat diperlukan untuk cek interaksi"}
        
        interactions = []
        checked_pairs = set()
        
        for i, med_a in enumerate(med_list):
            for med_b in med_list[i+1:]:
                pair = tuple(sorted([med_a.lower(), med_b.lower()]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                # Check in simple_drug_interactions table
                interaction_query = text("""
                    SELECT drug_a, drug_b, severity, description, recommendation
                    FROM simple_drug_interactions 
                    WHERE is_active = 1
                    AND (
                        (LOWER(drug_a) LIKE :med_a AND LOWER(drug_b) LIKE :med_b) OR
                        (LOWER(drug_a) LIKE :med_b AND LOWER(drug_b) LIKE :med_a)
                    )
                """)
                
                result = db.execute(interaction_query, {
                    "med_a": f"%{med_a.lower()}%",
                    "med_b": f"%{med_b.lower()}%"
                }).fetchone()
                
                if result:
                    interactions.append({
                        "drug_a": result.drug_a,
                        "drug_b": result.drug_b,
                        "severity": result.severity,
                        "description": result.description,
                        "recommendation": result.recommendation
                    })
        
        return {
            "medications_checked": med_list,
            "interactions_found": len(interactions),
            "interactions": interactions,
            "risk_level": "high" if any(i["severity"] == "Major" for i in interactions) else 
                         "medium" if any(i["severity"] == "Moderate" for i in interactions) else "low"
        }
        
    except Exception as e:
        logger.error(f"Error checking drug interactions: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengecek interaksi obat")

@router.get("/patients/{patient_id}/medication-history")
async def get_patient_medication_history(
    patient_id: int,
    include_discontinued: bool = Query(False, description="Include discontinued medications"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get complete medication history for a patient"""
    try:
        where_conditions = ["p.id = :patient_id"]
        if not include_discontinued:
            where_conditions.append("pm.status = 'active'")
        
        where_clause = " AND ".join(where_conditions)
        
        history_query = text(f"""
            SELECT 
                pm.id,
                pm.medication_name,
                pm.dosage,
                pm.frequency,
                pm.start_date,
                pm.end_date,
                pm.status,
                pm.prescribed_by,
                pm.created_at,
                mr.diagnosis_text,
                mr.created_at as visit_date
            FROM patient_medications pm
            JOIN patients p ON pm.no_rm = p.no_rm
            LEFT JOIN medical_records mr ON pm.medical_record_id = mr.id
            WHERE {where_clause}
            ORDER BY pm.start_date DESC, pm.created_at DESC
            LIMIT :limit
        """)
        
        results = db.execute(history_query, {
            "patient_id": patient_id,
            "limit": limit
        }).fetchall()
        
        return {
            "patient_id": patient_id,
            "total_medications": len(results),
            "medication_history": [
                {
                    "id": row.id,
                    "medication_name": row.medication_name,
                    "dosage": row.dosage,
                    "frequency": row.frequency,
                    "start_date": row.start_date.isoformat() if row.start_date else None,
                    "end_date": row.end_date.isoformat() if row.end_date else None,
                    "status": row.status,
                    "prescribed_by": row.prescribed_by,
                    "prescribed_at": row.created_at.isoformat() if row.created_at else None,
                    "diagnosis": row.diagnosis_text,
                    "visit_date": row.visit_date.isoformat() if row.visit_date else None
                }
                for row in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting medication history for patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil riwayat obat pasien")
