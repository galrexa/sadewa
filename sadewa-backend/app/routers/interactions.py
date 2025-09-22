"""
Enhanced interactions router for SADEWA - Database Migration Version

Provides multi-layered clinical decision support with performance optimization
through database integration and fallback to JSON for reliability.
"""
# Standard library imports
import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Database imports
from app.database import get_db
from app.models import Patient, PatientMedication, PatientDiagnosis, DrugInteraction, PatientAllergy

# Third-party imports
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload

# Local application imports
from app.schemas import InteractionRequest, InteractionResponse, GroqTestResponse
from services.groq_service import groq_service

router = APIRouter()

# Simple in-memory cache for optimization (production: use Redis)
analysis_cache: Dict[str, Dict] = {}
CACHE_DURATION = timedelta(hours=1)  # Cache for 1 hour


async def load_drug_interactions(db: Session) -> List[Dict]:
    """Load drug interactions from database with fallback to JSON."""
    try:
        interactions = db.query(DrugInteraction).filter(
            DrugInteraction.is_active == True
        ).all()
        
        result = [
            {
                "id": interaction.id,
                "drug_a": interaction.drug_a,
                "drug_b": interaction.drug_b,
                "severity": interaction.severity.value,
                "mechanism": interaction.mechanism,
                "clinical_effect": interaction.clinical_effect,
                "recommendation": interaction.recommendation,
                "monitoring": interaction.monitoring
            }
            for interaction in interactions
        ]
        
        print(f"✅ Loaded {len(result)} drug interactions from database")
        return result
        
    except Exception as e:
        print(f"❌ Database error loading interactions: {e}")
        print("🔄 Falling back to JSON file...")
        return load_drug_interactions_from_json()


async def load_patients(db: Session) -> List[Dict]:
    """Load patients from database with optimized queries and JSON fallback."""
    try:
        patients = db.query(Patient)\
            .options(joinedload(Patient.medications))\
            .options(joinedload(Patient.diagnoses))\
            .options(joinedload(Patient.allergies))\
            .all()
        
        result = [
            {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender.value,
                "weight_kg": getattr(patient, 'weight_kg', 70.0),
                "current_medications": [
                    f"{med.medication_name} {med.dosage or ''}".strip()
                    for med in patient.medications if med.is_active
                ],
                "diagnoses_text": [
                    diag.diagnosis_text for diag in patient.diagnoses
                ],
                "allergies": [
                    allergy.allergen for allergy in patient.allergies
                ]
            }
            for patient in patients
        ]
        
        print(f"✅ Loaded {len(result)} patients from database")
        return result
        
    except Exception as e:
        print(f"❌ Database error loading patients: {e}")
        print("🔄 Falling back to JSON file...")
        return load_patients_from_json()


def load_drug_interactions_from_json() -> List[Dict]:
    """Fallback: Load drug interactions from JSON file."""
    file_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "drug_interactions.json"
    )
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Loaded {len(data)} drug interactions from JSON fallback")
            return data
    except FileNotFoundError:
        print("⚠️ JSON fallback file not found, using minimal data")
        return [{
            "id": 1,
            "drug_a": "Warfarin",
            "drug_b": "Ibuprofen",
            "severity": "MAJOR",
            "mechanism": "Increased anticoagulant effect",
            "clinical_effect": "Significantly increased bleeding risk",
            "recommendation": "Avoid combination. Use paracetamol instead.",
            "monitoring": "Monitor INR closely if must use together"
        }]


def load_patients_from_json() -> List[Dict]:
    """Fallback: Load patients from JSON file."""
    file_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "patients.json"
    )
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Loaded {len(data)} patients from JSON fallback")
            return data
    except FileNotFoundError:
        print("⚠️ JSON fallback file not found, using minimal data")
        return [{
            "id": "P001",
            "name": "Bapak Agus Santoso",
            "age": 72,
            "gender": "Male",
            "weight_kg": 68.5,
            "diagnoses_text": [
                "Atrial Fibrillation (chronic)",
                "Chronic Ischemic Heart Disease"
            ],
            "current_medications": [
                "Warfarin 5mg OD (for AF stroke prevention)",
                "Lisinopril 10mg OD (for hypertension)"
            ],
            "allergies": ["Penicillin (rash)"]
        }]


def create_cache_key(patient_id: int, medications: List[str], notes: str) -> str:
    """Create a unique cache key for an analysis request."""
    content = f"{patient_id}|{sorted(medications)}|{notes}"
    return hashlib.md5(content.encode()).hexdigest()


def is_cache_valid(timestamp: datetime) -> bool:
    """Check if a cache entry is still valid based on its timestamp."""
    return datetime.now() - timestamp < CACHE_DURATION


async def get_cached_analysis(cache_key: str) -> Optional[Dict]:
    """Get analysis from cache if it exists and is still valid."""
    if cache_key in analysis_cache:
        cached_data = analysis_cache[cache_key]
        if is_cache_valid(cached_data['timestamp']):
            cached_data['result']['from_cache'] = True
            return cached_data['result']
        # Remove expired cache entry
        del analysis_cache[cache_key]
    return None


def cache_analysis(cache_key: str, result: Dict) -> None:
    """Cache an analysis result with the current timestamp."""
    analysis_cache[cache_key] = {
        'timestamp': datetime.now(),
        'result': result.copy()
    }


def _create_timeout_fallback_response(patient_data: Dict, new_medications: List[str]) -> Dict:
    """Create fallback response when Groq API times out."""
    return {
        "analysis_timestamp": datetime.now().isoformat(),
        "patient_id": patient_data.get('id', 'Unknown'),
        "overall_risk_level": "MODERATE",
        "safe_to_prescribe": False,
        "warnings": [
            {
                "severity": "MODERATE",
                "type": "SYSTEM_ERROR",
                "drugs_involved": new_medications,
                "description": "Analysis timeout - unable to complete comprehensive interaction check",
                "clinical_significance": "Potential drug interactions not fully evaluated",
                "recommendation": "Manual pharmacist review recommended before prescribing",
                "monitoring_required": "Standard drug monitoring protocols"
            }
        ],
        "contraindications": [],
        "dosing_adjustments": [], 
        "monitoring_plan": ["Pharmacist consultation recommended"],
        "llm_reasoning": "Analysis timed out after 2.5 seconds. Manual review recommended to ensure patient safety.",
        "confidence_score": 0.0,
        "timeout_error": True
    }


def _enhance_analysis_result(
    result: Dict, patient_data: Dict, new_medications: List[str]
) -> Dict:
    """Enhance the AI analysis result with additional rule-based clinical context."""
    
    # Ensure required fields exist with the correct format
    for key, default_value in {
        'warnings': [], 'contraindications': [], 'dosing_adjustments': [],
        'monitoring_plan': []
    }.items():
        if key not in result or not isinstance(result[key], list):
            result[key] = default_value

    # VALIDASI dan PERBAIKI warnings - pastikan semua required fields ada
    for i, warning in enumerate(result.get('warnings', [])):
        if isinstance(warning, dict):
            # Pastikan semua required fields ada dengan default values
            result['warnings'][i] = {
                "severity": warning.get('severity', 'MODERATE'),
                "type": warning.get('type', 'SYSTEM_ERROR'),
                "drugs_involved": warning.get('drugs_involved', new_medications),
                "description": warning.get('description', 'Drug interaction detected'),
                "clinical_significance": warning.get('clinical_significance', 'Clinical assessment required'),
                "recommendation": warning.get('recommendation', 'Consult healthcare provider'),
                "monitoring_required": warning.get('monitoring_required', 'Standard monitoring')
            }

    # Validate and convert contraindications if they are strings
    if result['contraindications'] and isinstance(result['contraindications'][0], str):
        old_contraindications = result['contraindications']
        result['contraindications'] = []
        for contra_str in old_contraindications:
            result['contraindications'].append({
                "drug": "Unknown",
                "diagnosis": "Unknown", 
                "reason": contra_str,
                "alternative_suggested": None
            })

    # Validate and convert dosing_adjustments if they are strings  
    if result['dosing_adjustments'] and isinstance(result['dosing_adjustments'][0], str):
        old_adjustments = result['dosing_adjustments']
        result['dosing_adjustments'] = []
        for adj_str in old_adjustments:
            result['dosing_adjustments'].append({
                "drug": "Unknown",
                "standard_dose": "Standard dosing",
                "recommended_dose": "See clinical notes",
                "reason": adj_str
            })

    # Add patient age-related warnings if necessary (geriatric check)
    patient_age = patient_data.get('age', 0)
    if patient_age >= 65:
        pim_medications = ['ibuprofen', 'diclofenac', 'indomethacin', 'ketorolac']
        for med in new_medications:
            for pim in pim_medications:
                if pim.lower() in med.lower():
                    result['warnings'].append({
                        "severity": "MODERATE",
                        "type": "AGE_RELATED",
                        "drugs_involved": [med],
                        "description": f"Potentially inappropriate medication in elderly patient (age {patient_age})",
                        "clinical_significance": "Increased risk of adverse effects in geriatric population",
                        "recommendation": "Consider alternative medication or dose reduction",
                        "monitoring_required": "Enhanced monitoring for adverse effects"
                    })
                    
                    result['dosing_adjustments'].append({
                        "drug": med,
                        "standard_dose": "Adult dose",
                        "recommended_dose": "Reduce dose by 25-50% or consider alternative",
                        "reason": f"Age-related dose adjustment for {patient_age} year old patient"
                    })

    # Add kidney function warnings for nephrotoxic drugs if CKD is diagnosed
    diagnoses = patient_data.get('diagnoses_text', [])
    kidney_related = any('kidney' in diag.lower() or 'ginjal' in diag.lower() for diag in diagnoses)
    
    if kidney_related:
        nephrotoxic_drugs = ['ibuprofen', 'diclofenac', 'naproxen', 'metformin']
        for med in new_medications:
            for nephro in nephrotoxic_drugs:
                if nephro.lower() in med.lower():
                    result['contraindications'].append({
                        "drug": med,
                        "diagnosis": "Chronic Kidney Disease",
                        "reason": "Nephrotoxic medication contraindicated in kidney disease",
                        "alternative_suggested": "Paracetamol (if pain relief needed)"
                    })

    # Ensure required timestamp format
    if 'analysis_timestamp' not in result:
        result['analysis_timestamp'] = datetime.now().isoformat()
    
    return result


@router.post("/analyze-interactions", response_model=InteractionResponse)
async def analyze_interactions(
    request: InteractionRequest, 
    db: Session = Depends(get_db)
):
    """
    Run enhanced drug interaction analysis with multi-layered clinical
    decision support using database with JSON fallback.
    """
    start_time = time.time()
    cache_key = create_cache_key(
        request.patient_id, request.new_medications, request.notes or ""
    )

    try:
        # Check cache first for performance optimization
        cached_result = await get_cached_analysis(cache_key)
        if cached_result:
            print(f"✅ Cache hit for patient {request.patient_id}")
            return InteractionResponse(**cached_result)

        # Try database first, fallback to JSON if database unavailable
        try:
            patients = await load_patients(db)
            drug_interactions_db = await load_drug_interactions(db)
            data_source = "database"
        except Exception as db_error:
            print(f"⚠️ Database unavailable, using JSON fallback: {db_error}")
            patients = load_patients_from_json()
            drug_interactions_db = load_drug_interactions_from_json()
            data_source = "json_fallback"

        patient_data = next((p for p in patients if p["id"] == request.patient_id), None)
        if not patient_data:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {request.patient_id} not found in {data_source}"
            )

        # Enhanced AI analysis with timeout protection
        try:
            analysis_task = groq_service.analyze_drug_interactions(
                patient_data=patient_data,
                new_medications=request.new_medications,
                drug_interactions_db=drug_interactions_db,
                notes=request.notes or ""
            )
            analysis_result = await asyncio.wait_for(analysis_task, timeout=2.5)

        except asyncio.TimeoutError:
            # Fallback response if Groq API times out
            analysis_result = _create_timeout_fallback_response(
                patient_data, request.new_medications
            )

        # Add performance metadata and enhance the result
        processing_time = time.time() - start_time
        analysis_result['processing_time'] = round(processing_time, 3)
        analysis_result['from_cache'] = False
        analysis_result['data_source'] = data_source  # Track where data came from
        enhanced_result = _enhance_analysis_result(
            analysis_result, patient_data, request.new_medications
        )

        # Cache the new result
        cache_analysis(cache_key, enhanced_result)
        print(f"✅ Analysis completed for {request.patient_id} in {processing_time:.3f}s using {data_source}")

        return InteractionResponse(**enhanced_result)

    except HTTPException:
        raise  # Re-raise HTTPException to let FastAPI handle it
    except Exception as e:
        # Create comprehensive error response for the client
        processing_time = time.time() - start_time
        print(f"❌ Analysis failed for {request.patient_id}: {e}")
        
        error_response = {
            "analysis_timestamp": datetime.now().isoformat(),
            "patient_id": request.patient_id,
            "overall_risk_level": "MODERATE",  # Default to moderate for safety
            "safe_to_prescribe": False,
            "warnings": [
                {
                    "severity": "MAJOR",
                    "type": "SYSTEM_ERROR",
                    "drugs_involved": request.new_medications,
                    "description": "Unable to complete automated drug interaction analysis",
                    "clinical_significance": "Manual pharmacist review required before prescribing",
                    "recommendation": "Consult clinical pharmacist for manual drug interaction review",
                    "monitoring_required": "Manual assessment of all drug interactions"
                }
            ],
            "contraindications": [],
            "dosing_adjustments": [],
            "monitoring_plan": ["Manual pharmacist consultation required"],
            "llm_reasoning": f"System error prevented automated analysis: {e}. Manual review strongly recommended for patient safety.",
            "confidence_score": 0.0,
            "processing_time": round(processing_time, 3),
            "from_cache": False
        }
        
        return InteractionResponse(**error_response)


@router.get("/test-groq", response_model=GroqTestResponse)
async def test_groq_connection():
    """Test the Groq API connection and measure performance."""
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    try:
        result = await groq_service.test_connection()
        response_time = time.time() - start_time
        success = "GROQ_CONNECTION_OK" in result
        return GroqTestResponse(
            success=success,
            response=f"{result} (took {response_time:.3f}s)",
            error=None if success else "Unexpected response format from Groq.",
            timestamp=timestamp
        )
    except Exception as e:
        return GroqTestResponse(
            success=False,
            response=None,
            error=f"Connection failed: {str(e)}",
            timestamp=timestamp
        )


@router.get("/cache-stats")
async def get_cache_statistics():
    """Get cache statistics for performance monitoring."""
    total = len(analysis_cache)
    valid = sum(1 for c in analysis_cache.values() if is_cache_valid(c['timestamp']))
    hit_ratio = (valid / max(total, 1)) * 100
    return {
        "total_cached_analyses": total,
        "valid_cached_analyses": valid,
        "cache_hit_ratio": f"{hit_ratio:.1f}%",
        "cache_duration_hours": CACHE_DURATION.total_seconds() / 3600
    }


@router.delete("/clear-cache")
async def clear_analysis_cache():
    """Clear the analysis cache. Intended for development/testing."""
    global analysis_cache
    cleared_count = len(analysis_cache)
    analysis_cache = {}  # Re-assign to a new empty dict
    return {
        "message": "Cache cleared successfully",
        "items_cleared": cleared_count,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/data-source-status")
async def get_data_source_status(db: Session = Depends(get_db)):
    """Check status of data sources (database vs JSON fallback)."""
    try:
        # Test database connection
        patients_db = await load_patients(db)
        interactions_db = await load_drug_interactions(db) 
        
        return {
            "database_status": "available",
            "patients_count": len(patients_db),
            "interactions_count": len(interactions_db),
            "primary_source": "database",
            "fallback_available": True
        }
    except Exception as e:
        # Test JSON fallback
        patients_json = load_patients_from_json()
        interactions_json = load_drug_interactions_from_json()
        
        return {
            "database_status": f"unavailable: {e}",
            "patients_count": len(patients_json),
            "interactions_count": len(interactions_json),
            "primary_source": "json_fallback",
            "fallback_available": True
        }