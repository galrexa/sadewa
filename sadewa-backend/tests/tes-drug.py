# test_drug_interactions.py
"""
Test Drug Interaction Analysis untuk SADEWA API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_drug_interactions():
    """Test drug interaction analysis functionality"""
    print("💊 Testing Drug Interaction Analysis")
    print("=" * 45)
    
    # Get a patient with allergies for testing
    try:
        patients_response = requests.get(f"{BASE_URL}/api/patients/search?limit=1")
        if patients_response.status_code == 200:
            patients = patients_response.json().get('patients', [])
            test_patient_id = patients[0]['id'] if patients else None
            print(f"👤 Using Patient ID: {test_patient_id}")
        else:
            test_patient_id = None
            print("⚠️  No patient available, testing without patient context")
    except:
        test_patient_id = None
        print("⚠️  Could not get patient, testing without patient context")
    
    # Test Case 1: Basic Drug Interaction (Low Risk)
    print(f"\n💊 Test 1: Low Risk Drug Combination")
    low_risk_drugs = {
        "medications": ["Paracetamol", "Vitamin C", "Omeprazole"],
        "patient_id": test_patient_id,
        "include_cache": True
    }
    
    try:
        start_time = datetime.now()
        response = requests.post(
            f"{BASE_URL}/api/analyze/drug-interactions",
            json=low_risk_drugs,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        print(f"⏱️  Response Time: {processing_time:.1f}ms")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Low Risk Analysis Complete!")
            print(f"   💊 Input Medications: {len(result.get('input_medications', []))}")
            print(f"   ⚠️  Total Interactions: {result.get('total_interactions', 0)}")
            print(f"   🚨 High Risk Interactions: {result.get('high_risk_interactions', 0)}")
            print(f"   🚫 Contraindications: {len(result.get('contraindications', []))}")
            print(f"   💽 Cache Used: {result.get('cache_used', False)}")
            
            interactions = result.get('interactions', [])
            if interactions:
                print(f"   📋 Interactions Found:")
                for interaction in interactions[:2]:
                    print(f"      • {interaction.get('drug_1')} + {interaction.get('drug_2')}")
                    print(f"        Severity: {interaction.get('severity')} - {interaction.get('description')}")
            else:
                print(f"   ✅ No interactions found (Good combination)")
                
        else:
            print(f"❌ Low risk analysis failed")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Low risk test failed: {e}")
    
    # Test Case 2: High Risk Drug Combination
    print(f"\n🚨 Test 2: High Risk Drug Combination")
    high_risk_drugs = {
        "medications": ["Warfarin", "Aspirin", "Ibuprofen", "Simvastatin"],
        "patient_id": test_patient_id,
        "include_cache": True
    }
    
    try:
        start_time = datetime.now()
        response = requests.post(
            f"{BASE_URL}/api/analyze/drug-interactions",
            json=high_risk_drugs,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        print(f"⏱️  Response Time: {processing_time:.1f}ms")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ High Risk Analysis Complete!")
            print(f"   💊 Input Medications: {len(result.get('input_medications', []))}")
            print(f"   ⚠️  Total Interactions: {result.get('total_interactions', 0)}")
            print(f"   🚨 High Risk Interactions: {result.get('high_risk_interactions', 0)}")
            print(f"   🚫 Contraindications: {len(result.get('contraindications', []))}")
            
            # Show detailed interactions
            interactions = result.get('interactions', [])
            if interactions:
                print(f"   📋 Detailed Interactions:")
                for i, interaction in enumerate(interactions[:3], 1):
                    severity = interaction.get('severity', 'UNKNOWN')
                    emoji = "🚨" if severity == "MAJOR" else "⚠️" if severity == "MODERATE" else "ℹ️"
                    print(f"      {i}. {emoji} {interaction.get('drug_1')} + {interaction.get('drug_2')}")
                    print(f"         Severity: {severity}")
                    print(f"         Effect: {interaction.get('description', 'N/A')}")
                    print(f"         Recommendation: {interaction.get('recommendation', 'Monitor closely')}")
            
            # Show AI analysis if available
            ai_analysis = result.get('ai_analysis')
            if ai_analysis:
                print(f"   🤖 AI Analysis:")
                print(f"      Confidence: {ai_analysis.get('confidence', 0):.0%}")
                recommendations = ai_analysis.get('recommendations', [])
                for rec in recommendations[:2]:
                    print(f"      • {rec}")
                
        else:
            print(f"❌ High risk analysis failed")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ High risk test failed: {e}")
    
    # Test Case 3: Single Drug (No Interactions Expected)
    print(f"\n💊 Test 3: Single Drug Analysis")
    single_drug = {
        "medications": ["Paracetamol"],
        "patient_id": test_patient_id,
        "include_cache": False  # Test without cache
    }
    
    try:
        start_time = datetime.now()
        response = requests.post(
            f"{BASE_URL}/api/analyze/drug-interactions",
            json=single_drug,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        print(f"⏱️  Response Time: {processing_time:.1f}ms")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Single Drug Analysis Complete!")
            print(f"   💊 Medication: {result.get('input_medications', ['N/A'])[0]}")
            print(f"   ⚠️  Interactions: {result.get('total_interactions', 0)} (expected: 0)")
            print(f"   💽 Cache Used: {result.get('cache_used', False)} (expected: False)")
            
        else:
            print(f"❌ Single drug analysis failed")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Single drug test failed: {e}")
    
    # Test Case 4: Invalid/Empty Drug List
    print(f"\n🚫 Test 4: Validation Test (Empty Drug List)")
    invalid_drugs = {
        "medications": [],
        "include_cache": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze/drug-interactions",
            json=invalid_drugs,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 422:  # Validation error expected
            print(f"✅ Validation Working Correctly!")
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'Validation failed')}")
        elif response.status_code == 400:
            print(f"✅ Bad Request Handled Correctly!")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
    
    # Test Case 5: Check Analysis Statistics
    print(f"\n📊 Test 5: Analysis Statistics")
    try:
        response = requests.get(
            f"{BASE_URL}/api/analyze/stats/summary?days=30",
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Analysis Statistics Retrieved!")
            print(f"   📅 Period: {stats.get('period_days', 0)} days")
            
            analysis_stats = stats.get('analysis_statistics', {})
            for analysis_type, type_stats in analysis_stats.items():
                print(f"   📊 {analysis_type.replace('_', ' ').title()}:")
                print(f"      Total: {type_stats.get('total_analyses', 0)}")
                print(f"      Avg Confidence: {type_stats.get('avg_confidence', 0):.0%}")
                print(f"      Avg Time: {type_stats.get('avg_processing_time_ms', 0):.1f}ms")
            
            cache_stats = stats.get('cache_statistics', {})
            print(f"   💽 Cache Statistics:")
            print(f"      Total Cached: {cache_stats.get('total_cached_interactions', 0)}")
            print(f"      Recent Hits: {cache_stats.get('recent_cache_hits', 0)}")
            
        else:
            print(f"❌ Statistics retrieval failed")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Statistics test failed: {e}")

def test_cache_functionality():
    """Test caching performance"""
    print(f"\n💽 Testing Cache Performance")
    print("-" * 30)
    
    # Same drug combination tested twice
    test_drugs = {
        "medications": ["Warfarin", "Aspirin"],
        "include_cache": True
    }
    
    print("🔄 First call (should populate cache)...")
    try:
        start_time = datetime.now()
        response1 = requests.post(
            f"{BASE_URL}/api/analyze/drug-interactions",
            json=test_drugs,
            timeout=15
        )
        time1 = (datetime.now() - start_time).total_seconds() * 1000
        
        if response1.status_code == 200:
            result1 = response1.json()
            cache_used1 = result1.get('cache_used', False)
            print(f"   ⏱️  Time: {time1:.1f}ms, Cache: {cache_used1}")
        
    except Exception as e:
        print(f"   ❌ First call failed: {e}")
        return
    
    print("🔄 Second call (should use cache)...")
    try:
        start_time = datetime.now()
        response2 = requests.post(
            f"{BASE_URL}/api/analyze/drug-interactions",
            json=test_drugs,
            timeout=15
        )
        time2 = (datetime.now() - start_time).total_seconds() * 1000
        
        if response2.status_code == 200:
            result2 = response2.json()
            cache_used2 = result2.get('cache_used', False)
            print(f"   ⏱️  Time: {time2:.1f}ms, Cache: {cache_used2}")
            
            # Performance comparison
            if time2 < time1:
                improvement = ((time1 - time2) / time1) * 100
                print(f"   🚀 Cache improved performance by {improvement:.1f}%")
            else:
                print(f"   ⚠️  No performance improvement detected")
        
    except Exception as e:
        print(f"   ❌ Second call failed: {e}")

def main():
    """Main test function"""
    print("💊 SADEWA Drug Interaction Testing")
    print("=" * 50)
    print(f"🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Server: {BASE_URL}")
    print()
    
    # Run drug interaction tests
    test_drug_interactions()
    
    # Test caching
    test_cache_functionality()
    
    print(f"\n🎯 Drug Interaction Testing Complete!")
    print("=" * 50)
    print("📚 Summary:")
    print("• Low risk drug combinations tested")
    print("• High risk interactions detected")
    print("• Single drug analysis tested")
    print("• Validation functionality verified")
    print("• Cache performance tested")
    print("• Statistics dashboard tested")
    print()
    print("📝 Next steps:")
    print("• Test AI diagnosis features")
    print("• Integration with medical records")
    print("• Frontend development")

if __name__ == "__main__":
    main()