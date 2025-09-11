from fastapi import APIRouter, HTTPException
from typing import List
import json
import os
from app.schemas import PatientResponse

router = APIRouter()

# Load patients data from JSON file
def load_patients():
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "patients.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@router.get("/patients", response_model=List[PatientResponse])
async def get_all_patients():
    """Get list of all patients"""
    patients = load_patients()
    return patients

@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient_by_id(patient_id: str):
    """Get specific patient by ID"""
    patients = load_patients()
    
    for patient in patients:
        if patient["id"] == patient_id:
            return patient
    
    raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found")

@router.get("/patients/search/{name}")
async def search_patients_by_name(name: str):
    """Search patients by name"""
    patients = load_patients()
    
    results = []
    for patient in patients:
        if name.lower() in patient["name"].lower():
            results.append(patient)
    
    return {
        "query": name,
        "results": results,
        "count": len(results)
    }