# sadewa-backend/app/schemas.py
"""
SADEWA API Schemas - FIXED with proper imports
Extended schemas untuk patient management
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# === PATIENT SCHEMAS ===
class PatientBase(BaseModel):
    """Base schema untuk Patient"""
    name: str = Field(..., description="Nama pasien")
    age: int = Field(..., ge=0, le=150, description="Umur pasien")
    gender: str = Field(..., description="Jenis kelamin (male/female)")
    phone: Optional[str] = Field(None, description="Nomor telepon")


class PatientCreate(PatientBase):
    """Schema untuk create patient baru"""
    pass


class PatientUpdate(BaseModel):
    """Schema untuk update patient"""
    name: Optional[str] = Field(None, description="Nama pasien")
    age: Optional[int] = Field(None, ge=0, le=150, description="Umur pasien")
    gender: Optional[str] = Field(None, description="Jenis kelamin")
    phone: Optional[str] = Field(None, description="Nomor telepon")


class PatientResponse(BaseModel):
    """Schema untuk response patient data"""
    id: int = Field(..., description="ID pasien")
    name: str = Field(..., description="Nama pasien")
    age: int = Field(..., description="Umur pasien")
    gender: str = Field(..., description="Jenis kelamin")
    phone: Optional[str] = Field(None, description="Nomor telepon")
    created_at: datetime = Field(..., description="Tanggal dibuat")
    updated_at: datetime = Field(..., description="Tanggal update")
    
    class Config:
        from_attributes = True


# === MEDICAL RECORD SCHEMAS ===
class MedicalRecordBase(BaseModel):
    """Base schema untuk Medical Record"""
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Teks diagnosis")
    medications: List[str] = Field(default_factory=list, description="Daftar obat")
    notes: Optional[str] = Field(None, description="Catatan")


class MedicalRecordCreate(MedicalRecordBase):
    """Schema untuk create medical record baru"""
    patient_id: int = Field(..., description="ID pasien")


class MedicalRecordUpdate(BaseModel):
    """Schema untuk update medical record"""
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Teks diagnosis")
    medications: Optional[List[str]] = Field(None, description="Daftar obat")
    notes: Optional[str] = Field(None, description="Catatan")


class MedicalRecordResponse(BaseModel):
    """Schema untuk response medical record"""
    id: int = Field(..., description="ID record")
    patient_id: int = Field(..., description="ID pasien")
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Teks diagnosis")
    medications: List[str] = Field(default_factory=list, description="Daftar obat")
    interactions: Optional[Dict] = Field(None, description="Data interaksi")
    notes: Optional[str] = Field(None, description="Catatan")
    created_at: datetime = Field(..., description="Tanggal dibuat")
    updated_at: datetime = Field(..., description="Tanggal update")
    
    class Config:
        from_attributes = True


class PatientDetailResponse(PatientResponse):
    """Schema untuk response patient dengan medical records"""
    medical_records: List[MedicalRecordResponse] = Field(
        default_factory=list, 
        description="Riwayat medis"
    )


# === API RESPONSE SCHEMAS ===
class PatientListResponse(BaseModel):
    """Schema untuk response list patients"""
    patients: List[PatientResponse] = Field(..., description="Daftar pasien")
    total: int = Field(..., description="Total pasien")
    page: int = Field(1, description="Halaman saat ini")
    limit: int = Field(10, description="Limit per halaman")


class SaveDiagnosisRequest(BaseModel):
    """Schema untuk save diagnosis dari existing drug analysis"""
    patient_id: int = Field(..., description="ID pasien")
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Teks diagnosis")
    medications: List[str] = Field(..., description="Daftar obat yang dianalisis")
    interaction_results: Optional[Dict] = Field(None, description="Hasil analisis interaksi")
    notes: Optional[str] = Field(None, description="Catatan klinis")


# === ICD10 SCHEMAS (untuk compatibility dengan existing routers) ===
class ICD10Result(BaseModel):
    """Schema untuk hasil pencarian ICD-10"""
    code: str = Field(..., description="Kode ICD-10")
    name_id: str = Field(..., description="Nama dalam bahasa Indonesia")
    name_en: Optional[str] = Field(None, description="Nama dalam bahasa Inggris")
    category: Optional[str] = Field(None, description="Kategori")


class ICD10Search(BaseModel):
    """Schema untuk request pencarian ICD-10"""
    query: str = Field(..., description="Query pencarian")
    limit: Optional[int] = Field(10, description="Limit hasil")


# === DRUG SCHEMAS (untuk compatibility) ===
class DrugSearchResponse(BaseModel):
    """Schema untuk hasil pencarian obat"""
    id: int = Field(..., description="ID obat")
    nama_obat: str = Field(..., description="Nama obat")
    nama_obat_internasional: str = Field(..., description="Nama internasional")
    display_name: str = Field(..., description="Nama untuk display")


# === INTERACTION SCHEMAS (untuk compatibility) ===
class InteractionRequest(BaseModel):
    """Schema untuk request analisis interaksi"""
    patient_id: str = Field(..., description="ID pasien")
    new_medications: List[str] = Field(..., description="Daftar obat baru")
    notes: Optional[str] = Field("", description="Catatan tambahan")