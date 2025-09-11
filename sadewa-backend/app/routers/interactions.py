"""
Enhanced interactions router untuk SADEWA - DAY 2
Multi-layered clinical decision support dengan performance optimization
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
import json
import os
import time
import hashlib
import asyncio
from datetime import datetime, timedelta

from app.schemas import InteractionRequest, InteractionResponse, GroqTestResponse
from services.groq_service import groq_service

router = APIRouter()

# Simple in-memory cache untuk optimization (production: gunakan Redis)
analysis_cache = {}
CACHE_DURATION = timedelta(hours=1)  # Cache selama 1 jam

def load_drug_interactions() -> List[Dict]:
    """Load enhanced drug interactions database"""
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "drug_interactions.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return fallback data jika file tidak ada
        return [
            {
                "id": 1,
                "drug_a": "Warfarin",
                "drug_b": "Ibuprofen", 
                "severity": "MAJOR",
                "mechanism": "Increased anticoagulant effect",
                "clinical_effect": "Significantly increased bleeding risk",
                "recommendation": "Avoid combination. Use paracetamol instead.",
                "monitoring": "Monitor INR closely if must use together"
            }
        ]

def load_patients() -> List[Dict]:
    """Load patients database"""
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "patients.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return P001 fallback data untuk test case
        return [
            {
                "id": "P001",
                "name": "Bapak Agus Santoso",
                "age": 72,
                "gender": "Male",
                "weight_kg": 68.5,
                "diagnoses_text": [
                    "Atrial Fibrillation (chronic)",
                    "Chronic Ischemic Heart Disease",
                    "Chronic knee pain (osteoarthritis suspected)"
                ],
                "current_medications": [
                    "Warfarin 5mg OD (for AF stroke prevention)",
                    "Lisinopril 10mg OD (for hypertension)",
                    "Metformin 500mg BID (for diabetes control)"
                ],
                "allergies": ["Penicillin (rash)"]
            }
        ]

def create_cache_key(patient_id: str, medications: List[str], notes: str) -> str:
    """Buat cache key untuk request yang sama"""
    content = f"{patient_id}|{sorted(medications)}|{notes}"
    return hashlib.md5(content.encode()).hexdigest()

def is_cache_valid(timestamp: datetime) -> bool:
    """Check apakah cache masih valid"""
    return datetime.now() - timestamp < CACHE_DURATION

async def get_cached_analysis(cache_key: str) -> Optional[Dict]:
    """Get analysis dari cache jika masih valid"""
    if cache_key in analysis_cache:
        cached_data = analysis_cache[cache_key]
        if is_cache_valid(cached_data['timestamp']):
            cached_data['result']['from_cache'] = True
            return cached_data['result']
        else:
            # Remove expired cache
            del analysis_cache[cache_key]
    return None

def cache_analysis(cache_key: str, result: Dict) -> None:
    """Cache analysis result"""
    analysis_cache[cache_key] = {
        'timestamp': datetime.now(),
        'result': result.copy()
    }

@router.post("/analyze-interactions", response_model=InteractionResponse)
async def analyze_interactions(request: InteractionRequest):
    """
    Enhanced drug interaction analysis dengan multi-layered clinical decision support
    
    Fitur DAY 2:
    - Advanced prompt engineering
    - Multi-layered analysis (drug-drug, drug-disease, age-related)
    - Performance optimization dengan caching
    - Comprehensive clinical recommendations
    """
    
    start_time = time.time()
    
    try:
        # Create cache key
        cache_key = create_cache_key(request.patient_id, request.new_medications, request.notes or "")
        
        # Check cache first untuk performance optimization
        cached_result = await get_cached_analysis(cache_key)
        if cached_result:
            print(f"✅ Cache hit for patient {request.patient_id}")
            return InteractionResponse(**cached_result)
        
        # Find patient data
        patients = load_patients()
        patient_data = None
        
        for patient in patients:
            if patient["id"] == request.patient_id:
                patient_data = patient
                break
        
        if not patient_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Patient {request.patient_id} not found in database"
            )
        
        # Load enhanced drug interactions database
        drug_interactions_db = load_drug_interactions()
        
        # Enhanced AI analysis dengan timeout protection
        try:
            # Set timeout untuk Groq API call (2.5 detik untuk memenuhi target <3s total)
            analysis_task = groq_service.analyze_drug_interactions(
                patient_data=patient_data,
                new_medications=request.new_medications,
                drug_interactions_db=drug_interactions_db,
                notes=request.notes or ""
            )
            
            analysis_result = await asyncio.wait_for(analysis_task, timeout=2.5)
            
        except asyncio.TimeoutError:
            # Fallback response jika Groq API timeout
            analysis_result = _create_timeout_fallback_response(patient_data, request.new_medications)
        
        # Add performance metadata
        processing_time = time.time() - start_time
        analysis_result['processing_time'] = round(processing_time, 3)
        analysis_result['from_cache'] = False
        
        # Validate dan enhance response
        enhanced_result = _enhance_analysis_result(analysis_result, patient_data, request.new_medications)
        
        # Cache result untuk request yang sama di masa depan
        cache_analysis(cache_key, enhanced_result)
        
        # Log successful analysis
        print(f"✅ Analysis completed for {request.patient_id} in {processing_time:.3f}s")
        
        return InteractionResponse(**enhanced_result)
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Analysis failed for {request.patient_id}: {str(e)}")
        
        # Create comprehensive error response
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
            "llm_reasoning": f"System error prevented automated analysis: {str(e)}. Manual review strongly recommended for patient safety.",
            "confidence_score": 0.0,
            "error": True,
            "error_message": str(e),
            "processing_time": round(processing_time, 3),
            "from_cache": False
        }
        
        raise HTTPException(status_code=500, detail=error_response)

def _create_timeout_fallback_response(patient_data: Dict, new_medications: List[str]) -> Dict:
    """Create fallback response when Groq API times out"""
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

def _enhance_analysis_result(result: Dict, patient_data: Dict, new_medications: List[str]) -> Dict:
    """Enhance analysis result dengan additional clinical context"""
    
    # Ensure required fields exist
    if 'warnings' not in result:
        result['warnings'] = []
    if 'contraindications' not in result:
        result['contraindications'] = []
    if 'monitoring_plan' not in result:
        result['monitoring_plan'] = []
    
    # Add patient age-related warnings jika diperlukan
    patient_age = patient_data.get('age', 0)
    if patient_age >= 65:
        # Check for potentially inappropriate medications in elderly
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
                        "recommendation": "Consider alternative medication or lower dose",
                        "monitoring_required": "Enhanced monitoring for adverse effects"
                    })
    
    # Add kidney function considerations jika ada creatinine data
    current_meds = patient_data.get('current_medications', [])
    if any('metformin' in med.lower() for med in current_meds):
        result['monitoring_plan'].append("Monitor kidney function (eGFR) regularly")
    
    return result

@router.get("/test-groq", response_model=GroqTestResponse)
async def test_groq_connection():
    """Test enhanced Groq API connection dengan performance measurement"""
    start_time = time.time()
    
    try:
        result = await groq_service.test_connection()
        response_time = time.time() - start_time
        
        return GroqTestResponse(
            status="success" if "GROQ_CONNECTION_OK" in result else "warning",
            response=result,
            response_time=round(response_time, 3)
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        return GroqTestResponse(
            status="error",
            response=f"Connection failed: {str(e)}",
            response_time=round(response_time, 3)
        )

@router.get("/cache-stats")
async def get_cache_statistics():
    """Get cache statistics untuk monitoring performance"""
    total_cached = len(analysis_cache)
    valid_cached = sum(1 for cached_data in analysis_cache.values() 
                      if is_cache_valid(cached_data['timestamp']))
    
    return {
        "total_cached_analyses": total_cached,
        "valid_cached_analyses": valid_cached,
        "cache_hit_ratio": f"{(valid_cached/max(total_cached, 1)*100):.1f}%",
        "cache_duration_hours": CACHE_DURATION.total_seconds() / 3600
    }

@router.delete("/clear-cache")
async def clear_analysis_cache():
    """Clear analysis cache - untuk development/testing"""
    global analysis_cache
    cleared_count = len(analysis_cache)
    analysis_cache.clear()
    
    return {
        "message": f"Cache cleared successfully",
        "items_cleared": cleared_count,
        "timestamp": datetime.now().isoformat()
    }