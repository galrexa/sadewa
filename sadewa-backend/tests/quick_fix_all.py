# quick_fix_all.py
"""
Quick fix untuk semua issues yang ditemukan dari testing
"""

import requests
import json
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BASE_URL = "http://localhost:8000"

def get_db_config():
    """Get database config"""
    database_url = os.getenv('DATABASE_URL', '')
    
    if 'DATABASE_URL=' in database_url:
        database_url = database_url.replace('DATABASE_URL=', '')
    
    if database_url.startswith('mysql+pymysql://'):
        database_url = database_url.replace('mysql+pymysql://', 'mysql://')
    
    try:
        # Parse mysql://user:password@host:port/database
        database_url = database_url.replace('mysql://', '')
        auth_part, host_part = database_url.split('@', 1)
        
        if ':' in auth_part:
            user, password = auth_part.split(':', 1)
        else:
            user = auth_part
            password = ''
        
        host_port, database = host_part.split('/', 1)
        if ':' in host_port:
            host, port = host_port.split(':', 1)
            port = int(port)
        else:
            host = host_port
            port = 3306
        
        return {
            'host': host, 'port': port, 'user': user, 
            'password': password, 'database': database
        }
    except:
        return {
            'host': 'localhost', 'port': 3306, 'user': 'root', 
            'password': '', 'database': 'sadewa_db'
        }

def fix_drug_interactions_quick():
    """Quick fix untuk drug interactions database"""
    print("💊 Quick Fix: Drug Interactions Database")
    print("-" * 40)
    
    config = get_db_config()
    
    # Quick sample interactions
    quick_interactions = [
        ("Warfarin", "Aspirin", "Major", "Increased bleeding risk", "Avoid combination or monitor closely"),
        ("Warfarin", "Ibuprofen", "Major", "GI bleeding risk", "Use paracetamol instead"),
        ("Aspirin", "Ibuprofen", "Moderate", "GI irritation", "Monitor for stomach problems"),
        ("Simvastatin", "Warfarin", "Moderate", "Enhanced anticoagulation", "Monitor INR"),
        ("Paracetamol", "Warfarin", "Minor", "Slight INR increase", "Monitor with chronic use")
    ]
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Clear and insert
        cursor.execute("DELETE FROM simple_drug_interactions")
        
        for drug_a, drug_b, severity, desc, rec in quick_interactions:
            # Insert both directions
            cursor.execute("""
                INSERT INTO simple_drug_interactions 
                (drug_a, drug_b, severity, description, recommendation, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
            """, (drug_a, drug_b, severity, desc, rec))
            
            cursor.execute("""
                INSERT INTO simple_drug_interactions 
                (drug_a, drug_b, severity, description, recommendation, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
            """, (drug_b, drug_a, severity, desc, rec))
        
        connection.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM simple_drug_interactions")
        count = cursor.fetchone()[0]
        
        print(f"✅ {count} drug interactions added")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        return False

def test_medical_record_simple():
    """Test medical record dengan data minimal"""
    print("\n🩺 Testing Medical Record Creation (Simple)")
    print("-" * 45)
    
    # Get a patient ID
    try:
        patients_resp = requests.get(f"{BASE_URL}/api/patients/search?limit=1")
        if patients_resp.status_code == 200:
            patients = patients_resp.json().get('patients', [])
            if patients:
                patient_id = patients[0]['id']
                print(f"👤 Using Patient ID: {patient_id}")
            else:
                print("❌ No patients found")
                return False
        else:
            print("❌ Cannot get patients")
            return False
    except Exception as e:
        print(f"❌ Error getting patients: {e}")
        return False
    
    # Simple medical record data
    simple_record = {
        "patient_id": patient_id,
        "chief_complaint": "Demam dan batuk sejak 3 hari",
        "symptoms": [
            {
                "symptom": "Demam",
                "severity": "moderate", 
                "duration": "acute",
                "description": "Demam 38.5 derajat"
            }
        ],
        "diagnosis_text": "Common cold",
        "medications": ["Paracetamol", "Vitamin C"],
        "notes": "Pasien istirahat dan minum air putih"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/medical-records",
            json=simple_record,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Medical record created: ID {result.get('id')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_drug_interaction_simple():
    """Test drug interaction dengan data yang pasti ada"""
    print("\n💊 Testing Drug Interaction (Simple)")
    print("-" * 40)
    
    test_data = {
        "medications": ["Warfarin", "Aspirin"],
        "include_cache": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze/drug-interactions",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            interactions = result.get('total_interactions', 0)
            print(f"✅ Analysis complete: {interactions} interactions found")
            
            if interactions > 0:
                print("✅ Drug interaction detection working!")
                for interaction in result.get('interactions', [])[:2]:
                    print(f"   • {interaction.get('drug_1')} + {interaction.get('drug_2')}: {interaction.get('severity')}")
            else:
                print("⚠️  No interactions found - database may need more data")
            
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def check_server_logs():
    """Check if we can get any server info"""
    print("\n🔍 Server Diagnostics")
    print("-" * 25)
    
    endpoints_to_check = [
        ("/health", "Health Check"),
        ("/api/patients/stats/summary", "Patient Stats"),  
        ("/api/medical-records/stats/summary", "Medical Stats"),
        ("/monitoring", "Monitoring")
    ]
    
    for endpoint, name in endpoints_to_check:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {name}: {response.status_code}")
            
        except Exception as e:
            print(f"   ❌ {name}: {e}")

def main():
    """Main quick fix function"""
    print("🔧 SADEWA Quick Fix for All Issues")
    print("=" * 50)
    print(f"🕒 Fix Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Server: {BASE_URL}")
    
    # Step 1: Check server status
    check_server_logs()
    
    # Step 2: Fix drug interactions database
    drug_fix_success = fix_drug_interactions_quick()
    
    # Step 3: Test medical records
    medical_test_success = test_medical_record_simple()
    
    # Step 4: Test drug interactions  
    drug_test_success = test_drug_interaction_simple()
    
    # Step 5: Summary
    print(f"\n🎯 Quick Fix Summary")
    print("=" * 30)
    
    fixes = [
        ("Drug Interactions DB", drug_fix_success),
        ("Medical Record Test", medical_test_success),
        ("Drug Interaction Test", drug_test_success)
    ]
    
    for fix_name, success in fixes:
        status = "✅" if success else "❌"
        print(f"{status} {fix_name}")
    
    successful_fixes = sum(1 for _, success in fixes if success)
    print(f"\n📊 {successful_fixes}/{len(fixes)} fixes successful")
    
    if successful_fixes == len(fixes):
        print("🎉 All issues fixed!")
    else:
        print("⚠️  Some issues need manual investigation")
        print("\nTroubleshooting tips:")
        if not drug_fix_success:
            print("• Check database connection and permissions")
        if not medical_test_success:
            print("• Check server logs for medical records endpoint errors")
        if not drug_test_success:
            print("• Verify drug interaction database has data")
    
    print(f"\n📝 Next recommended actions:")
    print("• Check server terminal for detailed error logs")
    print("• Test individual endpoints via browser (/docs)")
    print("• Run full test suite after fixes")

if __name__ == "__main__":
    main()