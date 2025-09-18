# sadewa-backend/app/models.py
"""
SQLAlchemy Models untuk SADEWA - Extended
Tambahan: Patient dan MedicalRecord models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class GenderEnum(enum.Enum):
    male = "male"
    female = "female"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    medical_records = relationship("MedicalRecord", back_populates="patient")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    diagnosis_code = Column(String(10), index=True)
    diagnosis_text = Column(String(500))
    medications = Column(JSON)
    interactions = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    patient = relationship("Patient", back_populates="medical_records")


# Existing Drug model (reference - already exists)
class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    nama_obat = Column(String(255), nullable=False)
    nama_obat_internasional = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ICD-10 model (missing model)
class ICD10(Base):
    __tablename__ = "icds"

    code = Column(String(255), primary_key=True)  # code adalah PK, bukan id
    name_en = Column(Text, nullable=False)
    name_id = Column(Text, nullable=False)