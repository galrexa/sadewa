# app/models.py
"""
✅ FIXED: SQLAlchemy Models for SADEWA using no_rm as foreign key
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, JSON, Enum as SQLEnum, ForeignKey, func, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum
from datetime import datetime, date

Base = declarative_base()

# ===== ENUMS =====

class GenderEnum(str, Enum):
    male = "male"
    female = "female"

class SeverityEnum(str, Enum):
    MAJOR = "MAJOR"
    MODERATE = "MODERATE"
    MINOR = "MINOR"

class MedicationStatusEnum(str, Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"

class EventTypeEnum(str, Enum):
    REGISTRATION = "registration"
    VISIT = "visit"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    LAB_RESULT = "lab_result"

# ===== MAIN MODELS =====

class Patient(Base):
    """✅ FIXED: Patient model with no_rm as primary key"""
    __tablename__ = "patients"

    id = Column(Integer, index=True)  # Keep for backward compatibility
    no_rm = Column(String(50), primary_key=True, index=True)  # ✅ PRIMARY KEY
    name = Column(String(255), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(SQLEnum(GenderEnum), nullable=False)
    phone = Column(String(20))
    weight_kg = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # AI-related fields
    medical_history = Column(JSON, comment='Riwayat penyakit untuk AI analysis')
    risk_factors = Column(JSON, comment='Faktor risiko untuk AI assessment')
    last_ai_analysis = Column(DateTime, comment='Timestamp terakhir AI analysis')
    ai_risk_score = Column(DECIMAL(3,2), default=0.00, comment='AI-generated risk score (0-10)')

    # ✅ FIXED: Relationships using no_rm
    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("PatientMedication", back_populates="patient", cascade="all, delete-orphan")
    diagnoses = relationship("PatientDiagnosis", back_populates="patient", cascade="all, delete-orphan")
    allergies = relationship("PatientAllergy", back_populates="patient", cascade="all, delete-orphan")
    timeline_entries = relationship("PatientTimeline", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(no_rm='{self.no_rm}', name='{self.name}')>"

class MedicalRecord(Base):
    """✅ FIXED: Medical record using no_rm foreign key"""
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False, index=True)  # Keep for backward compatibility
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=True)  # ✅ NEW FK
    diagnosis_code = Column(String(10), index=True)
    diagnosis_text = Column(String(500))
    medications = Column(JSON, comment='Prescribed medications (historical)')
    interactions = Column(JSON, comment='Visit data and interactions')
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # AI-enhanced fields
    symptoms = Column(JSON, comment='Structured symptoms data for AI')
    ai_suggestions = Column(JSON, comment='AI-generated diagnostic suggestions')
    ai_confidence = Column(DECIMAL(5,2), comment='AI confidence score (0-100)')
    differential_diagnosis = Column(JSON, comment='AI differential diagnosis')
    drug_interaction_alerts = Column(JSON, comment='AI-detected drug interactions')
    ai_processed_at = Column(DateTime, comment='When AI processed this record')

    # ✅ FIXED: Relationship
    patient = relationship("Patient", back_populates="medical_records")
    prescribed_medications = relationship("PatientMedication", back_populates="medical_record")

    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, patient_no_rm='{self.no_rm}')>"

class PatientMedication(Base):
    """✅ NEW: Current and historical medications using no_rm"""
    __tablename__ = "patient_medications"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    start_date = Column(Date, default=date.today)
    end_date = Column(Date, nullable=True)
    status = Column(SQLEnum(MedicationStatusEnum), default=MedicationStatusEnum.ACTIVE)
    prescribed_by = Column(String(255))
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)  # Backward compatibility
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="medications")
    medical_record = relationship("MedicalRecord", back_populates="prescribed_medications")

    def __repr__(self):
        return f"<PatientMedication(id={self.id}, medication='{self.medication_name}', status='{self.status}')>"

class PatientAllergy(Base):
    """✅ FIXED: Patient allergies using no_rm"""
    __tablename__ = "patient_allergies"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)
    allergen = Column(String(255), nullable=False)
    reaction_type = Column(String(100))
    severity = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    patient = relationship("Patient", back_populates="allergies")

    def __repr__(self):
        return f"<PatientAllergy(allergen='{self.allergen}', severity='{self.severity}')>"

class PatientDiagnosis(Base):
    """✅ FIXED: Patient diagnoses using no_rm"""
    __tablename__ = "patient_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)
    icd_code = Column(String(10), ForeignKey("icds.code"))
    diagnosis_text = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="diagnoses")
    icd = relationship("ICD10", back_populates="patient_diagnoses")

    def __repr__(self):
        return f"<PatientDiagnosis(icd_code='{self.icd_code}', diagnosis='{self.diagnosis_text}')>"

class PatientTimeline(Base):
    """✅ FIXED: Patient timeline using no_rm for better tracking"""
    __tablename__ = "patient_timeline"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)  # ✅ Use no_rm
    patient_id = Column(Integer, nullable=False)  # Keep for backward compatibility
    event_type = Column(SQLEnum(EventTypeEnum), nullable=False)
    event_date = Column(DateTime, nullable=False)
    event_data = Column(JSON, nullable=False, comment='Event details')
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="timeline_entries")
    medical_record = relationship("MedicalRecord")

    def __repr__(self):
        return f"<PatientTimeline(event_type='{self.event_type}', date='{self.event_date}')>"

# ===== DRUG AND INTERACTION MODELS =====

class Drug(Base):
    """Drug master data"""
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    nama_obat = Column(String(255), nullable=False)
    nama_obat_internasional = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Drug(nama_obat='{self.nama_obat}')>"

class DrugInteraction(Base):
    """Drug interaction data"""
    __tablename__ = "drug_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_a = Column(String(255), nullable=False, index=True)
    drug_b = Column(String(255), nullable=False, index=True)
    severity = Column(SQLEnum(SeverityEnum), nullable=False)
    description = Column(Text)
    mechanism = Column(Text)
    clinical_effect = Column(Text)
    recommendation = Column(Text)
    monitoring = Column(Text)
    evidence_level = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<DrugInteraction('{self.drug_a}' + '{self.drug_b}', severity='{self.severity}')>"

class SimpleDrugInteraction(Base):
    """Simplified drug interaction for quick lookups"""
    __tablename__ = "simple_drug_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_a = Column(String(255), nullable=False, comment='Nama obat pertama')
    drug_b = Column(String(255), nullable=False, comment='Nama obat kedua')
    severity = Column(SQLEnum('Major', 'Moderate', 'Minor', name='simple_severity'), nullable=False)
    description = Column(Text, nullable=False, comment='Deskripsi interaksi')
    recommendation = Column(Text, comment='Rekomendasi penanganan')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<SimpleDrugInteraction('{self.drug_a}' + '{self.drug_b}')>"

class DrugInteractionCache(Base):
    """Cache for drug interaction results"""
    __tablename__ = "drug_interaction_cache"

    id = Column(Integer, primary_key=True, index=True)
    drug_combination_hash = Column(String(64), nullable=False, comment='Hash dari kombinasi obat')
    drug_names = Column(JSON, nullable=False, comment='Array nama obat')
    interaction_result = Column(JSON, nullable=False, comment='Hasil analisis interaksi')
    severity_max = Column(SQLEnum(SeverityEnum), comment='Severity tertinggi')
    last_checked = Column(DateTime, server_default=func.now(), onupdate=func.now())
    expiry_date = Column(DateTime, nullable=False, comment='Cache expiry')

    def __repr__(self):
        return f"<DrugInteractionCache(hash='{self.drug_combination_hash}')>"

# ===== ICD10 AND DIAGNOSTIC MODELS =====

class ICD10(Base):
    """ICD-10 diagnostic codes"""
    __tablename__ = "icds"

    code = Column(String(255), primary_key=True)
    name_en = Column(Text, nullable=False)
    name_id = Column(Text, nullable=False)
    category = Column(String(100))  # A00-B99, C00-D48, etc.

    # Relationship back to patient diagnoses
    patient_diagnoses = relationship("PatientDiagnosis", back_populates="icd")

    def __repr__(self):
        return f"<ICD10(code='{self.code}', name_id='{self.name_id[:50]}...')>"

# ===== AI AND LOGGING MODELS =====

class AIAnalysisLog(Base):
    """Log untuk semua AI analysis"""
    __tablename__ = "ai_analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)  # ✅ Use no_rm
    patient_id = Column(Integer, nullable=False)  # Keep for backward compatibility
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"))
    analysis_type = Column(SQLEnum('diagnosis', 'drug_interaction', 'risk_assessment', 'treatment_recommendation', name='analysis_type'), nullable=False)
    input_data = Column(JSON, nullable=False, comment='Input yang diberikan ke AI')
    ai_response = Column(JSON, nullable=False, comment='Full AI response')
    confidence_score = Column(DECIMAL(5,2), comment='AI confidence score')
    processing_time_ms = Column(Integer, comment='Processing time in milliseconds')
    ai_model_version = Column(String(50), comment='AI model version used')
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    patient = relationship("Patient")
    medical_record = relationship("MedicalRecord")

    def __repr__(self):
        return f"<AIAnalysisLog(type='{self.analysis_type}', confidence={self.confidence_score})>"

# ===== TABLE CONFIGURATION =====

# Add table args for MySQL optimization
Patient.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

MedicalRecord.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

PatientMedication.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

PatientAllergy.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

PatientDiagnosis.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

PatientTimeline.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

Drug.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

DrugInteraction.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

SimpleDrugInteraction.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

ICD10.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

AIAnalysisLog.__table_args__ = (
    {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
)

# ===== UTILITY FUNCTIONS =====

def get_patient_by_no_rm(db_session, no_rm: str) -> Patient:
    """Get patient by no_rm"""
    return db_session.query(Patient).filter(Patient.no_rm == no_rm).first()

def get_current_medications(db_session, no_rm: str) -> list:
    """Get current active medications for patient"""
    return db_session.query(PatientMedication).filter(
        PatientMedication.no_rm == no_rm,
        PatientMedication.status == MedicationStatusEnum.ACTIVE,
        PatientMedication.is_active == True
    ).order_by(PatientMedication.start_date.desc()).all()

def get_patient_allergies(db_session, no_rm: str) -> list:
    """Get patient allergies"""
    return db_session.query(PatientAllergy).filter(
        PatientAllergy.no_rm == no_rm
    ).all()

def search_drugs(db_session, query: str, limit: int = 10) -> list:
    """Search drugs by name"""
    return db_session.query(Drug).filter(
        Drug.is_active == True,
        (Drug.nama_obat.ilike(f"%{query}%") | 
         Drug.nama_obat_internasional.ilike(f"%{query}%"))
    ).limit(limit).all()

def check_drug_interactions(db_session, drug_names: list) -> list:
    """Check for drug interactions"""
    interactions = []
    
    for i, drug_a in enumerate(drug_names):
        for drug_b in drug_names[i+1:]:
            interaction = db_session.query(SimpleDrugInteraction).filter(
                SimpleDrugInteraction.is_active == True,
                (
                    (SimpleDrugInteraction.drug_a.ilike(f"%{drug_a}%") & 
                     SimpleDrugInteraction.drug_b.ilike(f"%{drug_b}%")) |
                    (SimpleDrugInteraction.drug_a.ilike(f"%{drug_b}%") & 
                     SimpleDrugInteraction.drug_b.ilike(f"%{drug_a}%"))
                )
            ).first()
            
            if interaction:
                interactions.append(interaction)
    
    return interactions

# ===== MODEL VALIDATION =====

def validate_patient_data(patient_data: dict) -> dict:
    """Validate patient data before insert/update"""
    errors = {}
    
    if not patient_data.get('no_rm'):
        errors['no_rm'] = 'Nomor rekam medis wajib diisi'
    
    if not patient_data.get('name'):
        errors['name'] = 'Nama pasien wajib diisi'
    
    if not patient_data.get('age') or patient_data.get('age') <= 0:
        errors['age'] = 'Umur harus lebih dari 0'
    
    if patient_data.get('gender') not in ['male', 'female']:
        errors['gender'] = 'Jenis kelamin harus male atau female'
    
    return errors

def validate_medication_data(medication_data: dict) -> dict:
    """Validate medication data"""
    errors = {}
    
    if not medication_data.get('medication_name'):
        errors['medication_name'] = 'Nama obat wajib diisi'
    
    if not medication_data.get('dosage'):
        errors['dosage'] = 'Dosis obat wajib diisi'
    
    if not medication_data.get('frequency'):
        errors['frequency'] = 'Frekuensi obat wajib diisi'
    
    return errors