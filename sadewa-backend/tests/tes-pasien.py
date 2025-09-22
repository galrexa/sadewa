# debug_patient_registration.py
"""
Debug script untuk troubleshoot patient registration endpoint
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

def test_basic_connectivity():
    """Test basic server connectivity"""
    print("🔌 Testing basic connectivity...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_patient_registration_simple():
    """Test dengan data minimal"""
    print("\n📝 Testing simple patient registration...")
    
    simple_data = {
        "name": "Test Patient",
        "age": 30,
        "gender": "male"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/patients/register",
            json=simple_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            result = response.json()
            print(f"   Patient ID: {result.get('id')}")
            print(f"   Patient Code: {result.get('patient_code')}")
            return result
        else:
            print(f"❌ Registration failed!")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - server took too long to respond")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not reachable")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_patient_registration_full():
    """Test dengan data lengkap"""
    print("\n📋 Testing full patient registration...")
    
    full_data = {
        "name": "Jane Doe Complete",
        "age": 28,
        "gender": "female",
        "phone": "081234567890",
        "weight_kg": 55,
        "medical_history": ["Hipertensi", "Diabetes"],
        "allergies": ["Penisilin", "Aspirin"],
        "risk_factors": ["Merokok", "Kurang olahraga"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/patients/register",
            json=full_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Full registration successful!")
            result = response.json()
            print(f"   Patient ID: {result.get('id')}")
            print(f"   Processing Time: {result.get('processing_time_ms')}ms")
            return result
        else:
            print(f"❌ Full registration failed!")
            try:
                error_data = response.json()
                print(f"   Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Error Text: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Full registration error: {e}")
        return None

def test_patient_validation():
    """Test validation dengan data invalid"""
    print("\n🚫 Testing validation with invalid data...")
    
    invalid_cases = [
        {
            "name": "Invalid Age Test",
            "data": {"name": "Test", "age": -5, "gender": "male"},
            "expected_error": "age validation"
        },
        {
            "name": "Invalid Gender Test", 
            "data": {"name": "Test", "age": 30, "gender": "unknown"},
            "expected_error": "gender validation"
        },
        {
            "name": "Missing Required Field",
            "data": {"age": 30, "gender": "male"},
            "expected_error": "missing name"
        },
        {
            "name": "Empty Name",
            "data": {"name": "", "age": 30, "gender": "male"},
            "expected_error": "empty name"
        }
    ]
    
    for case in invalid_cases:
        print(f"\n   Testing: {case['name']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/patients/register",
                json=case['data'],
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 422:  # Validation error
                print(f"   ✅ Validation working - Status: {response.status_code}")
                error_detail = response.json()
                print(f"   Error: {error_detail.get('detail', 'Unknown validation error')}")
            elif response.status_code == 400:
                print(f"   ✅ Bad request handled - Status: {response.status_code}")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Test error: {e}")

def test_patient_search():
    """Test search functionality"""
    print("\n🔍 Testing patient search...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/patients/search?q=Test&limit=5",
            timeout=5
        )
        
        print(f"Search Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search successful!")
            print(f"   Total patients found: {result.get('total', 0)}")
            print(f"   Patients returned: {len(result.get('patients', []))}")
            
            # Show first patient if any
            patients = result.get('patients', [])
            if patients:
                first_patient = patients[0]
                print(f"   First patient: {first_patient.get('name')} (ID: {first_patient.get('id')})")
        else:
            print(f"❌ Search failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Search error: {e}")

def test_endpoint_availability():
    """Test semua endpoint yang dibutuhkan untuk patient registration"""
    print("\n🌐 Testing endpoint availability...")
    
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/docs", "API documentation"),
        ("GET", "/api/patients/search", "Patient search"),
        ("POST", "/api/patients/register", "Patient registration"),
        ("GET", "/api/patients/stats/summary", "Patient statistics")
    ]
    
    for method, path, description in endpoints:
        try:
            url = f"{BASE_URL}{path}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                # For POST endpoints, just check if they exist (might return 422 for missing data)
                response = requests.post(url, json={}, timeout=5)
            
            # Consider various success status codes
            if response.status_code in [200, 201, 422, 404]:
                status = "✅" if response.status_code in [200, 201] else "⚠️"
                print(f"   {status} {description}: {response.status_code}")
            else:
                print(f"   ❌ {description}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}: {e}")

def test_database_tables():
    """Test database tables existence via API"""
    print("\n🗄️  Testing database via API...")
    
    try:
        # Test patient statistics (indicates database connectivity)
        response = requests.get(f"{BASE_URL}/api/patients/stats/summary", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Database accessible via API")
            print(f"   Total patients in DB: {stats.get('total_patients', 0)}")
            print(f"   Male patients: {stats.get('gender_distribution', {}).get('male', 0)}")
            print(f"   Female patients: {stats.get('gender_distribution', {}).get('female', 0)}")
        else:
            print(f"❌ Database stats failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Database test error: {e}")

def main():
    """Main debug function"""
    print("🔧 SADEWA Patient Registration Debug")
    print("=" * 50)
    print(f"🎯 Target server: {BASE_URL}")
    print(f"⏰ Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Basic connectivity
    if not test_basic_connectivity():
        print("\n❌ Basic connectivity failed. Server might not be running.")
        return
    
    # Test 2: Endpoint availability
    test_endpoint_availability()
    
    # Test 3: Database connectivity
    test_database_tables()
    
    # Test 4: Simple registration
    patient1 = test_patient_registration_simple()
    
    # Test 5: Full registration
    patient2 = test_patient_registration_full()
    
    # Test 6: Validation testing
    test_patient_validation()
    
    # Test 7: Search functionality
    test_patient_search()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 DEBUG SUMMARY")
    print("=" * 50)
    
    if patient1 or patient2:
        print("✅ Patient registration is working!")
        if patient1:
            print(f"   Simple registration: Patient ID {patient1.get('id')}")
        if patient2:
            print(f"   Full registration: Patient ID {patient2.get('id')}")
    else:
        print("❌ Patient registration is not working!")
        print("\nTroubleshooting steps:")
        print("1. Check server logs for detailed error messages")
        print("2. Verify database connection and tables")
        print("3. Check if endpoint routing is correct")
        print("4. Validate request data format")
    
    print(f"\n🔗 Test completed at: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    # Check if requests library is available
    try:
        import requests
    except ImportError:
        print("❌ requests library not installed")
        print("Run: pip install requests")
        exit(1)
    
    main()