"""
SADEWA API Schemas

Defines the Pydantic models for data validation and serialization,
including extended schemas for patient management and interaction analysis.
"""
# Standard library imports
from datetime import datetime
from typing import Dict, List, Optional

# Third-party imports
from pydantic import BaseModel, Field


# === PATIENT SCHEMAS ===
class PatientBase(BaseModel):
    """Base schema for Patient."""
    name: str = Field(..., description="Nama pasien")
    age: int = Field(..., ge=0, le=150, description="Umur pasien")
    gender: str = Field(..., description="Jenis kelamin (male/female)")
    phone: Optional[str] = Field(None, description="Nomor telepon")


class PatientCreate(PatientBase):
    """Schema to create a new patient."""


class PatientUpdate(BaseModel):
    """Schema to update a patient."""
    name: Optional[str] = Field(None, description="Nama pasien")
    age: Optional[int] = Field(None, ge=0, le=150, description="Umur pasien")
    gender: Optional[str] = Field(None, description="Jenis kelamin")
    phone: Optional[str] = Field(None, description="Nomor telepon")


class PatientResponse(BaseModel):
    """Schema for patient data response."""
    no_rm: str = Field(..., description="Nomor Rekam Medis")
    id: int = Field(..., description="ID Legacy")
    name: str = Field(..., description="Nama pasien")
    age: int = Field(..., description="Umur pasien")
    gender: str = Field(..., description="Jenis kelamin")
    phone: Optional[str] = Field(None, description="Nomor telepon")
    created_at: datetime = Field(..., description="Tanggal dibuat")
    updated_at: datetime = Field(..., description="Tanggal update")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


# === MEDICAL RECORD SCHEMAS ===
class MedicalRecordBase(BaseModel):
    """Base schema for a Medical Record."""
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Teks diagnosis")
    medications: List[str] = Field(default_factory=list, description="Daftar obat")
    notes: Optional[str] = Field(None, description="Catatan")


class MedicalRecordCreate(MedicalRecordBase):
    """Schema to create a new medical record."""
    no_rm: str = Field(..., description="No Rekam Medis pasien")


class MedicalRecordUpdate(BaseModel):
    """Schema to update a medical record."""
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Teks diagnosis")
    medications: Optional[List[str]] = Field(None, description="Daftar obat")
    notes: Optional[str] = Field(None, description="Catatan")


class MedicalRecordResponse(BaseModel):
    """Schema for a medical record response."""
    id: int = Field(..., description="ID record")
    no_rm: str = Field(..., description="No Rekam Medis")
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Teks diagnosis")
    medications: List[str] = Field(default_factory=list, description="Daftar obat")
    interactions: Optional[Dict] = Field(None, description="Data interaksi")
    notes: Optional[str] = Field(None, description="Catatan")
    created_at: datetime = Field(..., description="Tanggal dibuat")
    updated_at: datetime = Field(..., description="Tanggal update")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PatientDetailResponse(PatientResponse):
    """Schema for patient response with their medical records."""
    medical_records: List[MedicalRecordResponse] = Field(
        default_factory=list,
        description="Riwayat medis"
    )


# === API RESPONSE SCHEMAS ===
class PatientListResponse(BaseModel):
    """Schema for a list of patients response."""
    patients: List[PatientResponse] = Field(..., description="Daftar pasien")
    total: int = Field(..., description="Total pasien")
    page: int = Field(1, description="Halaman saat ini")
    limit: int = Field(10, description="Limit per halaman")


class SaveDiagnosisRequest(BaseModel):
    """Schema to save a diagnosis from an existing drug analysis."""
    patient_id: int = Field(..., description="ID pasien")
    diagnosis_code: Optional[str] = Field(None, description="Kode ICD-10")
    diagnosis_text: Optional[str] = Field(None, description="Teks diagnosis")
    medications: List[str] = Field(..., description="Daftar obat yang dianalisis")
    interaction_results: Optional[Dict] = Field(None, description="Hasil analisis interaksi")
    notes: Optional[str] = Field(None, description="Catatan klinis")

class ICD10Result(BaseModel):
    """Schema for ICD-10 search results."""
    code: str = Field(..., description="Kode ICD-10")
    name_id: str = Field(..., description="Nama dalam bahasa Indonesia")
    name_en: Optional[str] = Field(None, description="Nama dalam bahasa Inggris")
    category: Optional[str] = Field(None, description="Kategori")


class ICD10Search(BaseModel):
    """Schema for an ICD-10 search request."""
    query: str = Field(..., description="Query pencarian")
    limit: Optional[int] = Field(10, description="Limit hasil")


# === DRUG SCHEMAS (for compatibility) ===
class DrugSearchResponse(BaseModel):
    """Schema for drug search results."""
    id: int = Field(..., description="ID obat")
    nama_obat: str = Field(..., description="Nama obat")
    nama_obat_internasional: str = Field(..., description="Nama internasional")
    display_name: str = Field(..., description="Nama untuk display")


# === INTERACTION SCHEMAS (for compatibility) ===
class InteractionRequest(BaseModel):
    patient_id: str = Field(..., description="Nomor Rekam Medis pasien")  # String sekarang
    new_medications: List[str] = Field(..., description="List obat baru")
    diagnoses: Optional[List[str]] = Field(None, description="List ICD-10 codes")
    notes: Optional[str] = Field(None, description="Catatan tambahan")


# === INTERACTION RESPONSE SCHEMAS ===
class InteractionWarning(BaseModel):
    """Schema for an interaction warning."""
    severity: str = Field(..., description="Level severity: MAJOR/MODERATE/MINOR")
    type: str = Field(..., description="Tipe warning")
    drugs_involved: List[str] = Field(..., description="Obat yang terlibat")
    description: str = Field(..., description="Deskripsi warning")
    clinical_significance: str = Field(..., description="Signifikansi klinis")
    recommendation: str = Field(..., description="Rekomendasi")
    monitoring_required: Optional[str] = Field(None, description="Monitoring yang diperlukan")


class Contraindication(BaseModel):
    """Schema for contraindication details."""
    drug: str = Field(..., description="Nama obat")
    diagnosis: str = Field(..., description="Diagnosis terkait")
    reason: str = Field(..., description="Alasan kontraindikasi")
    alternative_suggested: Optional[str] = Field(None, description="Saran alternatif obat")


class DosingAdjustment(BaseModel):
    drug: str = Field(..., description="Nama obat")
    standard_dose: str = Field(..., description="Dosis standar")
    recommended_dose: str = Field(..., description="Dosis yang direkomendasikan")
    reason: str = Field(..., description="Alasan penyesuaian dosis")


class InteractionResponse(BaseModel):
    analysis_timestamp: str = Field(..., description="Timestamp analisis")
    patient_id: str = Field(..., description="Nomor Rekam Medis pasien")
    overall_risk_level: str = Field(..., description="Level risiko keseluruhan")
    safe_to_prescribe: bool = Field(..., description="Aman untuk diresepkan")
    confidence_score: Optional[float] = Field(None, description="Skor kepercayaan")
    warnings: List[InteractionWarning] = Field(default_factory=list, description="List warning")
    contraindications: List[Contraindication] = Field(
        default_factory=list, description="Kontraindikasi detail"
    )
    dosing_adjustments: List[DosingAdjustment] = Field(
        default_factory=list, description="Penyesuaian dosis detail"
    )
    monitoring_plan: List[str] = Field(default_factory=list, description="Rencana monitoring")
    llm_reasoning: Optional[str] = Field(None, description="Penalaran AI")
    processing_time: Optional[float] = Field(None, description="Waktu pemrosesan")
    from_cache: bool = Field(False, description="Dari cache atau tidak")


class GroqTestResponse(BaseModel):
    """Schema for the Groq API test response."""
    success: bool = Field(..., description="Status keberhasilan")
    response: Optional[str] = Field(None, description="Response dari Groq")
    error: Optional[str] = Field(None, description="Error message jika ada")
    timestamp: str = Field(..., description="Timestamp test")