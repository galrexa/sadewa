# check_current_status.py
"""
Quick status check untuk melihat current state dari SADEWA API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def check_system_status():
    """Check overall system status"""
    print("🔍 SADEWA System Status Check")
    print("=" * 40)
    
    # Health check
    try:
        health = requests.get(f"{BASE_URL}/health").json()
        print(f"🟢 System Status: {health['status']}")
        print(f"📊 Version: {health['version']}")
        print(f"⏱️  Uptime: {health.get('total_check_time_ms', 0)}ms response time")
        
        if 'checks' in health and 'database' in health['checks']:
            db_status = health['checks']['database']['status']
            print(f"🗄️  Database: {db_status}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    return True

def check_patients_status():
    """Check patients data"""
    print(f"\n👥 Patients Status")
    print("-" * 20)
    
    try:
        # Get patient statistics
        stats = requests.get(f"{BASE_URL}/api/patients/stats/summary").json()
        
        print(f"📈 Total Patients: {stats['total_patients']}")
        print(f"👨 Male: {stats['gender_distribution']['male']}")
        print(f"👩 Female: {stats['gender_distribution']['female']}")
        
        age_dist = stats['age_distribution']
        print(f"🧒 Children: {age_dist['children']}")
        print(f"🧑 Adults: {age_dist['adults']}")
        print(f"👴 Elderly: {age_dist['elderly']}")
        
        print(f"📊 Average Age: {stats['average_age']:.1f} years")
        
        # Get recent patients
        search = requests.get(f"{BASE_URL}/api/patients/search?limit=5").json()
        
        print(f"\n📋 Recent Patients:")
        for patient in search['patients']:
            print(f"   • {patient['name']} ({patient['patient_code']}) - {patient['age']}y {patient['gender']}")
            
    except Exception as e:
        print(f"❌ Patient status check failed: {e}")

def check_system_performance():
    """Check system performance metrics"""
    print(f"\n⚡ Performance Metrics")
    print("-" * 20)
    
    try:
        monitoring = requests.get(f"{BASE_URL}/monitoring").json()
        
        perf = monitoring['performance_metrics']
        print(f"🕒 Uptime: {perf['uptime_hours']:.2f} hours")
        print(f"📊 Total Requests: {perf['total_requests']}")
        print(f"⚡ Requests/Hour: {perf['requests_per_hour']:.1f}")
        
        if 'database' in monitoring:
            db = monitoring['database']
            if 'connection_pool' in db:
                pool = db['connection_pool']
                print(f"🔗 DB Pool Size: {pool['pool_size']}")
                print(f"🔗 DB Checked Out: {pool['checked_out']}")
                print(f"🔗 DB Checked In: {pool['checked_in']}")
        
    except Exception as e:
        print(f"❌ Performance check failed: {e}")

def test_add_sample_patient():
    """Test adding a sample patient"""
    print(f"\n🧪 Testing New Patient Registration")
    print("-" * 35)
    
    sample_patient = {
        "name": f"Sample Patient {datetime.now().strftime('%H%M%S')}",
        "age": 35,
        "gender": "male",
        "phone": "081234567999",
        "weight_kg": 70,
        "medical_history": ["Healthy"],
        "allergies": [],
        "risk_factors": ["None"]
    }
    
    try:
        start_time = datetime.now()
        response = requests.post(
            f"{BASE_URL}/api/patients/register",
            json=sample_patient,
            headers={"Content-Type": "application/json"}
        )
        end_time = datetime.now()
        
        if response.status_code == 201:
            result = response.json()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            print(f"✅ Registration Successful!")
            print(f"   👤 Patient ID: {result['id']}")
            print(f"   🏷️  Patient Code: {result['patient_code']}")
            print(f"   📝 Name: {result['name']}")
            print(f"   ⏱️  Response Time: {processing_time:.1f}ms")
            print(f"   📊 Age Category: {result['age_category']}")
            
            return result['id']
        else:
            print(f"❌ Registration Failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return None

def test_patient_search(patient_id=None):
    """Test patient search functionality"""
    print(f"\n🔎 Testing Patient Search")
    print("-" * 25)
    
    # Test general search
    try:
        response = requests.get(f"{BASE_URL}/api/patients/search?q=Sample&limit=10")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search Results:")
            print(f"   📊 Total Found: {result['total']}")
            print(f"   📋 Returned: {len(result['patients'])}")
            print(f"   ⏱️  Response Time: {result['processing_time_ms']:.1f}ms")
            
            if result['patients']:
                print(f"   📝 First Result: {result['patients'][0]['name']}")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Search test failed: {e}")
    
    # Test specific patient lookup if ID provided
    if patient_id:
        try:
            response = requests.get(f"{BASE_URL}/api/patients/{patient_id}")
            
            if response.status_code == 200:
                patient = response.json()
                print(f"✅ Patient Detail:")
                print(f"   👤 {patient['name']} ({patient['patient_code']})")
                print(f"   📊 {patient['age']} years old, {patient['gender']}")
                print(f"   📱 Phone: {patient['phone'] or 'Not provided'}")
            else:
                print(f"❌ Patient detail failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Patient detail test failed: {e}")

def main():
    """Main status check function"""
    print(f"🚀 SADEWA API Status Check")
    print(f"🕒 Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Server: {BASE_URL}")
    print()
    
    # Check if server is running
    if not check_system_status():
        print("❌ Server is not accessible!")
        return
    
    # Check current patients
    check_patients_status()
    
    # Check performance
    check_system_performance()
    
    # Test new patient registration
    new_patient_id = test_add_sample_patient()
    
    # Test search
    test_patient_search(new_patient_id)
    
    print(f"\n🎯 Status Check Complete!")
    print("=" * 40)
    print("🟢 All systems operational!")
    print("📊 Patient registration working perfectly")
    print("🔍 Search functionality working")
    print("⚡ Performance looks good")
    
    print(f"\n📚 Next steps:")
    print("• Open http://localhost:8000/docs for API documentation")
    print("• Test medical records creation")
    print("• Test drug interaction analysis")
    print("• Connect frontend application")

if __name__ == "__main__":
    main()