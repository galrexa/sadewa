"""
SADEWA API Schemas - DAY 2 
Minimal working version tanpa complex validators
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


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