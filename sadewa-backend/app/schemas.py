"""
SADEWA API Schemas - DAY 3 Fixed
Simplified schemas untuk table structure yang ada
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


# Enums
class RiskLevel(str, Enum):
    MAJOR = "MAJOR"
    MODERATE = "MODERATE" 
    MINOR = "MINOR"
    LOW = "LOW"


class WarningType(str, Enum):
    DRUG_INTERACTION = "DRUG_INTERACTION"
    CONTRAINDICATION = "CONTRAINDICATION"
    ALLERGY = "ALLERGY"
    AGE_RELATED = "AGE_RELATED"
    DOSING = "DOSING"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class SeverityLevel(str, Enum):
    MAJOR = "MAJOR"
    MODERATE = "MODERATE"
    MINOR = "MINOR"


# Core Request/Response Schemas
class InteractionRequest(BaseModel):
    """Request untuk analisis interaksi obat"""
    patient_id: str = Field(..., description="ID pasien")
    new_medications: List[str] = Field(..., description="Obat baru yang akan diresepkan")
    notes: Optional[str] = Field(None, description="Catatan klinis tambahan")


class WarningDetail(BaseModel):
    """Detail warning individual"""
    severity: str = Field(..., description="Tingkat keparahan")
    type: str = Field(..., description="Tipe warning")
    drugs_involved: List[str] = Field(..., description="Obat yang terlibat")
    description: str = Field(..., description="Deskripsi masalah")
    clinical_significance: str = Field(..., description="Signifikansi klinis")
    recommendation: str = Field(..., description="Rekomendasi")
    monitoring_required: str = Field(..., description="Monitoring yang diperlukan")


class ContraindicationDetail(BaseModel):
    """Detail kontraindikasi"""
    drug: str = Field(..., description="Nama obat")
    diagnosis: str = Field(..., description="Diagnosis terkait")
    reason: str = Field(..., description="Alasan kontraindikasi")
    alternative_suggested: Optional[str] = Field(None, description="Alternatif obat")


class DosingAdjustment(BaseModel):
    """Detail penyesuaian dosis"""
    drug: str = Field(..., description="Nama obat")
    standard_dose: str = Field(..., description="Dosis standar")
    recommended_dose: str = Field(..., description="Dosis yang direkomendasikan")
    reason: str = Field(..., description="Alasan penyesuaian")


class InteractionResponse(BaseModel):
    """Response analisis interaksi"""
    analysis_timestamp: str = Field(..., description="Timestamp analisis")
    patient_id: str = Field(..., description="ID pasien")
    overall_risk_level: str = Field(..., description="Level risiko keseluruhan")
    safe_to_prescribe: bool = Field(..., description="Apakah aman untuk diresepkan")
    warnings: List[WarningDetail] = Field(default_factory=list, description="Daftar warnings")
    contraindications: Optional[List[ContraindicationDetail]] = Field(default_factory=list, description="Kontraindikasi")
    dosing_adjustments: Optional[List[DosingAdjustment]] = Field(default_factory=list, description="Penyesuaian dosis")
    monitoring_plan: Optional[List[str]] = Field(default_factory=list, description="Rencana monitoring")
    llm_reasoning: str = Field(..., description="Reasoning dari AI")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    error: Optional[bool] = Field(False, description="Apakah ada error")
    error_message: Optional[str] = Field(None, description="Pesan error")
    processing_time: Optional[float] = Field(None, description="Waktu pemrosesan")
    from_cache: Optional[bool] = Field(False, description="Dari cache atau tidak")


# Patient Schemas (untuk kompatibilitas dengan existing code)
class PatientResponse(BaseModel):
    """Response untuk patient data"""
    id: str = Field(..., description="ID pasien")
    name: str = Field(..., description="Nama pasien")
    age: int = Field(..., description="Umur")
    gender: str = Field(..., description="Jenis kelamin")
    weight_kg: Optional[float] = Field(None, description="Berat badan")
    current_medications: List[str] = Field(default_factory=list, description="Obat saat ini")
    diagnoses_text: List[str] = Field(default_factory=list, description="Diagnosis")
    allergies: List[str] = Field(default_factory=list, description="Alergi")


# ICD-10 Schemas
class ICD10Result(BaseModel):
    """Hasil pencarian ICD-10"""
    code: str = Field(..., description="Kode ICD-10")
    name_id: str = Field(..., description="Nama dalam bahasa Indonesia")
    name_en: Optional[str] = Field(None, description="Nama dalam bahasa Inggris")


class ICD10Search(BaseModel):
    """Request pencarian ICD-10"""
    query: str = Field(..., description="Query pencarian")
    limit: Optional[int] = Field(10, description="Limit hasil")


# Health Check Schemas
class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Status sistem")
    timestamp: str = Field(..., description="Timestamp")
    version: str = Field("2.0.0", description="Versi aplikasi")
    database_status: Optional[str] = Field(None, description="Status database")


class GroqTestResponse(BaseModel):
    """Groq connection test response"""
    status: str = Field(..., description="Status koneksi")
    response: str = Field(..., description="Response dari Groq")
    response_time: Optional[float] = Field(None, description="Waktu response")


# Cache & Performance Schemas
class CacheStats(BaseModel):
    """Cache statistics"""
    total_cached_analyses: int = Field(..., description="Total analisis dalam cache")
    valid_cached_analyses: int = Field(..., description="Analisis cache yang valid")
    cache_hit_ratio: str = Field(..., description="Cache hit ratio")
    cache_duration_hours: float = Field(..., description="Durasi cache")


# Additional utility schemas
class PatientSummary(BaseModel):
    """Summary patient data"""
    id: str = Field(..., description="ID pasien")
    name: str = Field(..., description="Nama pasien")
    age: int = Field(..., description="Umur")
    gender: str = Field(..., description="Jenis kelamin")
    weight_kg: Optional[float] = Field(None, description="Berat badan")


# Drug Schemas - SIMPLIFIED untuk table structure yang ada
class DrugBase(BaseModel):
    """Schema dasar untuk data obat."""
    nama_obat: str = Field(..., description="Nama obat dalam Bahasa Indonesia")
    nama_obat_internasional: str = Field(..., description="Nama obat internasional")


class DrugSearchResponse(BaseModel):
    """Schema untuk hasil pencarian obat - sesuai table drugs yang ada"""
    id: int = Field(..., description="ID obat")
    nama_obat: str = Field(..., description="Nama obat dalam Bahasa Indonesia")
    nama_obat_internasional: str = Field(..., description="Nama obat internasional")
    display_name: str = Field(..., description="Nama untuk display")

    class Config:
        from_attributes = True  # Pydantic v2 style


class DrugResponse(BaseModel):
    """Schema untuk detail obat - sesuai table structure yang ada"""
    id: int = Field(..., description="ID obat")
    nama_obat: str = Field(..., description="Nama obat dalam Bahasa Indonesia")
    nama_obat_internasional: str = Field(..., description="Nama obat internasional")
    is_active: bool = Field(..., description="Status aktif obat")
    created_at: Optional[datetime] = Field(None, description="Tanggal dibuat")

    class Config:
        from_attributes = True


class DrugInteractionResponse(BaseModel):
    """Schema untuk response interaksi obat - simple version"""
    drug_a: str = Field(..., description="Nama obat pertama")
    drug_b: str = Field(..., description="Nama obat kedua")
    severity: str = Field(..., description="Tingkat keparahan")
    description: str = Field(..., description="Deskripsi interaksi")
    recommendation: Optional[str] = Field(None, description="Rekomendasi")
    input_drugs: List[str] = Field(..., description="Input drugs dari user")

    class Config:
        from_attributes = True


class DrugStatsResponse(BaseModel):
    """Schema untuk statistik database obat"""
    total_drugs: int = Field(..., description="Total obat dalam database")
    total_interactions: int = Field(..., description="Total interaksi dalam database")
    sample_drugs: List[Dict[str, str]] = Field(..., description="Sample obat")
    database_status: str = Field(..., description="Status koneksi database")
    last_updated: str = Field(..., description="Tanggal update terakhir")


class DrugAutocompleteResponse(BaseModel):
    """Schema untuk autocomplete obat"""
    query: str = Field(..., description="Query yang dicari")
    suggestions: List[str] = Field(..., description="Daftar suggestions")


class DrugInteractionCheckResponse(BaseModel):
    """Schema untuk response check interactions"""
    input_drugs: List[str] = Field(..., description="Input drugs dari user")
    interactions_found: int = Field(..., description="Jumlah interaksi ditemukan")
    interactions: List[DrugInteractionResponse] = Field(..., description="Daftar interaksi")


class AddInteractionRequest(BaseModel):
    """Schema untuk request tambah interaksi manual"""
    drug_a: str = Field(..., description="Nama obat pertama")
    drug_b: str = Field(..., description="Nama obat kedua")
    severity: str = Field(..., description="Tingkat keparahan (Major/Moderate/Minor)")
    description: str = Field(..., description="Deskripsi interaksi")
    recommendation: Optional[str] = Field(None, description="Rekomendasi")


class AddInteractionResponse(BaseModel):
    """Schema untuk response tambah interaksi"""
    message: str = Field(..., description="Pesan sukses")
    drug_a: str = Field(..., description="Nama obat pertama")
    drug_b: str = Field(..., description="Nama obat kedua")
    severity: str = Field(..., description="Tingkat keparahan")