#!/usr/bin/env python3
"""
Quick test untuk memverifikasi endpoint drugs bekerja
Usage: python quick_test.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, params=None, expected_status=200):
    """Test single endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.request(method, url, params=params, timeout=5)
        
        success = response.status_code == expected_status
        status_icon = "✅" if success else "❌"
        
        print(f"{status_icon} {method} {endpoint} -> {response.status_code}")
        
        if success and response.content:
            try:
                data = response.json()
                if endpoint == "/api/drugs/stats":
                    print(f"   📊 Total drugs: {data.get('total_drugs', 0)}")
                elif endpoint == "/api/drugs/search":
                    print(f"   🔍 Found {len(data.get('drugs', []))} drugs")
                elif endpoint == "/health":
                    print(f"   💓 Status: {data.get('status', 'unknown')}")
            except:
                pass
        
        return success
        
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} -> Connection refused")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {method} {endpoint} -> Timeout")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} -> Error: {e}")
        return False

def main():
    """Run quick tests"""
    print("🚀 SADEWA Quick Endpoint Test")
    print("=" * 40)
    
    tests = [
        ("GET", "/health"),
        ("GET", "/api/drugs/stats"),
        ("GET", "/api/drugs/search", {"q": "para", "limit": 5}),
        ("GET", "/api/drugs/by-name", {"name": "Paracetamol"}),
        ("GET", "/api/drugs/popular", {"limit": 5}),
        ("GET", "/api/drugs/check-interactions", {"drug_names": "Warfarin,Ibuprofen"}),
        ("GET", "/api/drugs/validate", {"drug_names": "Paracetamol,Unknown Drug"}),
        ("GET", "/api/patients"),
        ("GET", "/api/icd10/search", {"q": "diabetes"})
    ]
    
    passed = 0
    total = len(tests)
    
    for test_data in tests:
        if len(test_data) == 3:
            method, endpoint, params = test_data
        else:
            method, endpoint = test_data
            params = None
            
        if test_endpoint(method, endpoint, params):
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All endpoints working!")
        print("\nNow you can:")
        print("1. Test frontend integration")
        print("2. Run complete test suite: python test_integration.py") 
        print("3. Start frontend: cd ../sadewa-frontend && npm run dev")
    else:
        print("⚠️  Some endpoints failed. Check backend logs.")
        print("\nTroubleshooting:")
        print("1. Ensure backend is running: python -m uvicorn main:app --reload")
        print("2. Check database connection")
        print("3. Verify all routers are imported correctly")

if __name__ == "__main__":
    main()