import enum

# Third-party imports
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"

class SeverityEnum(str, enum.Enum):
    """Enumeration for interaction severity levels."""
    MAJOR = "MAJOR"
    MODERATE = "MODERATE"
    MINOR = "MINOR"


class PatientMedication(Base):
    """Associates a medication with a patient."""
    __tablename__ = "patient_medications"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)  # ✅ GANTI
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    patient = relationship("Patient", back_populates="medications")

class PatientDiagnosis(Base):
    """Associates an ICD-10 diagnosis with a patient."""
    __tablename__ = "patient_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)  # ✅ GANTI
    icd_code = Column(String(10), ForeignKey("icds.code"))
    diagnosis_text = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="diagnoses")
    icd = relationship("ICD10", back_populates="patient_diagnoses")

class PatientAllergy(Base):
    """Records an allergy for a patient."""
    __tablename__ = "patient_allergies"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)  # ✅ GANTI
    allergen = Column(String(255), nullable=False)
    reaction_type = Column(String(100))
    severity = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    patient = relationship("Patient", back_populates="allergies")

class Patient(Base):
    """Represents a patient in the system."""
    __tablename__ = "patients"

    id = Column(Integer, index=True)  # Bukan primary key lagi
    no_rm = Column(String(50), primary_key=True, index=True)  # ✅ PRIMARY KEY
    name = Column(String(255), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    phone = Column(String(20))
    weight_kg = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships - sekarang menggunakan no_rm
    medical_records = relationship("MedicalRecord", back_populates="patient")
    medications = relationship("PatientMedication", back_populates="patient")
    diagnoses = relationship("PatientDiagnosis", back_populates="patient")
    allergies = relationship("PatientAllergy", back_populates="patient")

class MedicalRecord(Base):
    """Represents a single medical record entry for a patient."""
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    no_rm = Column(String(50), ForeignKey("patients.no_rm"), nullable=False)  # ✅ GANTI
    diagnosis_code = Column(String(10), index=True)
    diagnosis_text = Column(String(500))
    medications = Column(JSON)
    interactions = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    patient = relationship("Patient", back_populates="medical_records")


class DrugInteraction(Base):
    """Stores information about interactions between two drugs."""
    __tablename__ = "drug_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_a = Column(String(255), nullable=False, index=True)
    drug_b = Column(String(255), nullable=False, index=True)
    severity = Column(Enum(SeverityEnum), nullable=False)
    description = Column(Text)
    mechanism = Column(Text)
    clinical_effect = Column(Text)
    recommendation = Column(Text)
    monitoring = Column(Text)
    evidence_level = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # Add unique constraint to prevent duplicate interactions
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
    )


class Drug(Base):
    """Represents a drug available in the system."""
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    nama_obat = Column(String(255), nullable=False)
    nama_obat_internasional = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)


class ICD10(Base):
    """Represents an ICD-10 code and its description."""
    __tablename__ = "icds"

    code = Column(String(255), primary_key=True)
    name_en = Column(Text, nullable=False)
    name_id = Column(Text, nullable=False)
    category = Column(String(100))  # A00-B99, C00-D48, etc.

    # Relationship back to patient diagnoses
    patient_diagnoses = relationship("PatientDiagnosis", back_populates="icd")

    # Add index for faster searching
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
    )
