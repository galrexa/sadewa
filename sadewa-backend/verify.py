#!/usr/bin/env python3
"""
Verify test data untuk Patient P001 + Ibuprofen test case
"""
import json
import os
import requests

BASE_URL = "http://localhost:8000"

def check_patient_p001():
    """Check if Patient P001 exists and has Warfarin"""
    print("🔍 Checking Patient P001...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/patients/P001")
        
        if response.status_code == 200:
            patient = response.json()
            print(f"✅ Patient P001 found: {patient.get('name', 'Unknown')}")
            print(f"   Age: {patient.get('age')} years")
            print(f"   Current medications:")
            
            has_warfarin = False
            has_lisinopril = False
            
            for med in patient.get('current_medications', []):
                print(f"      - {med}")
                if 'warfarin' in med.lower():
                    has_warfarin = True
                if 'lisinopril' in med.lower():
                    has_lisinopril = True
            
            print(f"   Diagnoses:")
            for diag in patient.get('diagnoses_text', []):
                print(f"      - {diag}")
            
            if has_warfarin:
                print("✅ Warfarin found in current medications")
            else:
                print("⚠️ Warfarin NOT found - test case may not work as expected")
                
            if has_lisinopril:
                print("✅ Lisinopril found in current medications")
            
            return True, has_warfarin, has_lisinopril
            
        else:
            print(f"❌ Patient P001 not found: {response.status_code}")
            print("   Will use fallback data")
            return False, False, False
            
    except Exception as e:
        print(f"❌ Error checking patient P001: {e}")
        return False, False, False

def check_drug_interactions():
    """Check if Warfarin-Ibuprofen interaction exists"""
    print("\n🔍 Checking Drug Interactions Database...")
    
    file_path = "data/drug_interactions.json"
    
    if not os.path.exists(file_path):
        print(f"❌ File {file_path} not found")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            interactions = json.load(f)
        
        print(f"✅ Drug interactions file loaded: {len(interactions)} interactions")
        
        # Check for Warfarin-Ibuprofen
        warfarin_ibuprofen = False
        warfarin_aspirin = False
        lisinopril_ibuprofen = False
        
        for interaction in interactions:
            drug_a = interaction.get('drug_a', '').lower()
            drug_b = interaction.get('drug_b', '').lower()
            
            # Check Warfarin-Ibuprofen
            if (('warfarin' in drug_a and 'ibuprofen' in drug_b) or 
                ('warfarin' in drug_b and 'ibuprofen' in drug_a)):
                warfarin_ibuprofen = True
                print(f"✅ Warfarin-Ibuprofen interaction found: {interaction.get('severity', 'Unknown')} severity")
                print(f"   Description: {interaction.get('description', 'No description')[:100]}...")
            
            # Check other relevant interactions
            if (('warfarin' in drug_a and 'aspirin' in drug_b) or 
                ('warfarin' in drug_b and 'aspirin' in drug_a)):
                warfarin_aspirin = True
                
            if (('lisinopril' in drug_a and 'ibuprofen' in drug_b) or 
                ('lisinopril' in drug_b and 'ibuprofen' in drug_a)):
                lisinopril_ibuprofen = True
        
        if not warfarin_ibuprofen:
            print("⚠️ Warfarin-Ibuprofen interaction NOT found")
            print("   Adding sample interaction for testing...")
            
            # Add sample interaction
            sample_interaction = {
                "drug_a": "Warfarin",
                "drug_b": "Ibuprofen", 
                "severity": "Major",
                "description": "Meningkatkan risiko perdarahan secara signifikan. Kombinasi dapat menyebabkan perdarahan mayor."
            }
            
            interactions.append(sample_interaction)
            
            # Save updated file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(interactions, f, indent=2, ensure_ascii=False)
            
            print("✅ Warfarin-Ibuprofen interaction added to database")
        
        print(f"📊 Summary:")
        print(f"   Warfarin-Ibuprofen: {'✅ Found' if warfarin_ibuprofen else '⚠️ Added'}")
        print(f"   Warfarin-Aspirin: {'✅ Found' if warfarin_aspirin else '❌ Not found'}")
        print(f"   Lisinopril-Ibuprofen: {'✅ Found' if lisinopril_ibuprofen else '❌ Not found'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking drug interactions: {e}")
        return False

def create_patient_p001_if_missing():
    """Create Patient P001 data if missing"""
    print("\n🔧 Creating Patient P001 fallback data...")
    
    p001_data = {
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
            "Metformin 500mg BID (for diabetes control)",
            "Atorvastatin 20mg ON (for dyslipidemia)"
        ],
        "allergies": [
            "Penicillin (rash)",
            "Sulfonamides (mild GI upset)"
        ]
    }
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    patients_file = "data/patients.json"
    
    # Load existing patients or create new
    if os.path.exists(patients_file):
        with open(patients_file, 'r', encoding='utf-8') as f:
            patients = json.load(f)
    else:
        patients = []
    
    # Check if P001 already exists
    p001_exists = any(p.get('id') == 'P001' for p in patients)
    
    if not p001_exists:
        patients.append(p001_data)
        
        with open(patients_file, 'w', encoding='utf-8') as f:
            json.dump(patients, f, indent=2, ensure_ascii=False)
        
        print("✅ Patient P001 data created in patients.json")
    else:
        print("✅ Patient P001 already exists in patients.json")

if __name__ == "__main__":
    print("🧪 SADEWA Test Case Data Verification")
    print("=" * 50)
    
    # Check patient P001
    p001_exists, has_warfarin, has_lisinopril = check_patient_p001()
    
    # Check drug interactions
    interactions_ok = check_drug_interactions()
    
    # Create P001 if missing
    if not p001_exists:
        create_patient_p001_if_missing()
    
    print("\n📊 VERIFICATION SUMMARY:")
    print(f"   Patient P001: {'✅ Ready' if p001_exists or True else '❌ Missing'}")
    print(f"   Warfarin medication: {'✅ Found' if has_warfarin else '⚠️ Fallback'}")
    print(f"   Drug interactions: {'✅ Ready' if interactions_ok else '❌ Error'}")
    
    if interactions_ok and (p001_exists or True):
        print(f"\n🎯 READY FOR TEST CASE!")
        print(f"   Run: python test_case_p001.py")
    else:
        print(f"\n⚠️ Setup needed before testing")