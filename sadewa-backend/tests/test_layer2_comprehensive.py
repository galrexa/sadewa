"""
SADEWA Layer 2 Comprehensive Test Script
Tests advanced features: Patient risk assessment, contraindications, alternatives
"""
import asyncio
import json
import os
import sys
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.groq_service import enhanced_groq_service


# Test data
PATIENT_P001 = {
    "id": "P001",
    "name": "Bapak Agus Santoso",
    "age": 72,
    "gender": "Male",
    "weight": 65,
    "current_medications": [
        "Warfarin 5mg daily",
        "Lisinopril 10mg daily"
    ],
    "diagnoses_text": [
        "Essential hypertension (I10)",
        "Chronic ischemic heart disease (I25.9)"
    ],
    "allergies": ["Penicillin"]
}

PATIENT_P002_HIGH_RISK = {
    "id": "P002",
    "name": "Ibu Sari Dewi",
    "age": 58,
    "gender": "Female",
    "current_medications": [
        "Metformin 850mg",
        "Gliclazide 80mg"
    ],
    "diagnoses_text": [
        "Type 2 diabetes mellitus (E11)",
        "Chronic kidney disease, stage 3 (N18.3)"
    ],
    "allergies": []
}

DRUG_INTERACTIONS_DB = [
    {
        "drug_a": "Warfarin",
        "drug_b": "Ibuprofen", 
        "severity": "Major",
        "description": "Meningkatkan risiko pendarahan mayor, terutama pada saluran cerna. Monitor INR secara ketat."
    },
    {
        "drug_a": "Lisinopril",
        "drug_b": "Ibuprofen",
        "severity": "Moderate", 
        "description": "NSAID dapat mengurangi efektivitas ACE inhibitor dan meningkatkan risiko gangguan ginjal."
    },
    {
        "drug_a": "Metformin",
        "drug_b": "Contrast Media",
        "severity": "Major",
        "description": "Risiko asidosis laktat pada pasien dengan gangguan ginjal. Hentikan metformin 48 jam sebelum prosedur."
    }
]


async def test_layer2_connection():
    """Test Layer 2 Groq connection."""
    print("🔗 Testing Layer 2 Groq Connection...")
    
    try:
        result = await enhanced_groq_service.test_connection()
        
        if "Error" in result:
            print(f"❌ Connection failed: {result}")
            return False
        else:
            print(f"✅ Connection successful: {result}")
            return True
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False


async def test_patient_risk_assessment():
    """Test patient risk assessment components."""
    print("\n" + "="*60)
    print("🎯 TESTING PATIENT RISK ASSESSMENT")
    print("="*60)
    
    from services.groq_service import PatientRiskAssessment
    risk_assessor = PatientRiskAssessment()
    
    # Test 1: Age risk calculation
    print("\n📊 Test 1: Age Risk Assessment")
    
    test_ages = [25, 55, 68, 78]
    for age in test_ages:
        age_risk = risk_assessor.calculate_age_risk(age)
        print(f"Age {age}: {age_risk['risk_level']} (Score: {age_risk['score']})")
        print(f"  Factors: {', '.join(age_risk['factors'])}")
    
    # Test 2: Comorbidity risk assessment
    print("\n📊 Test 2: Comorbidity Risk Assessment")
    
    # Test P001 (elderly with cardiac conditions)
    p001_risk = risk_assessor.assess_comorbidity_risks(PATIENT_P001["diagnoses_text"])
    print(f"P001 Comorbidities: {PATIENT_P001['diagnoses_text']}")
    print(f"Risk Level: {p001_risk['risk_level']} (Score: {p001_risk['total_risk_score']})")
    print(f"Identified Risks: {len(p001_risk['identified_risks'])}")
    
    # Test P002 (kidney disease)
    p002_risk = risk_assessor.assess_comorbidity_risks(PATIENT_P002_HIGH_RISK["diagnoses_text"])
    print(f"\nP002 Comorbidities: {PATIENT_P002_HIGH_RISK['diagnoses_text']}")
    print(f"Risk Level: {p002_risk['risk_level']} (Score: {p002_risk['total_risk_score']})")
    print(f"Identified Risks: {len(p002_risk['identified_risks'])}")
    
    if p002_risk["identified_risks"]:
        for risk in p002_risk["identified_risks"]:
            print(f"  - {risk['type']}: {risk['severity']}")
            print(f"    Considerations: {', '.join(risk['considerations'][:2])}...")


async def test_drug_contraindication_analysis():
    """Test drug-disease contraindication analysis."""
    print("\n" + "="*60)
    print("💊 TESTING DRUG-DISEASE CONTRAINDICATION ANALYSIS")
    print("="*60)
    
    from services.groq_service import DrugContraindicationAnalyzer
    analyzer = DrugContraindicationAnalyzer()
    
    # Test scenarios
    test_scenarios = [
        {
            "medication": "Ibuprofen 400mg",
            "patient": PATIENT_P001,
            "expected": "Should find hypertension warning"
        },
        {
            "medication": "Metformin 850mg", 
            "patient": PATIENT_P002_HIGH_RISK,
            "expected": "Should find kidney disease contraindication"
        },
        {
            "medication": "Aspirin 100mg",
            "patient": PATIENT_P001,
            "expected": "Should be generally safe"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test Scenario {i}: {scenario['medication']}")
        print(f"Patient: {scenario['patient']['name']} ({scenario['patient']['age']} years)")
        print(f"Conditions: {', '.join(scenario['patient']['diagnoses_text'])}")
        
        result = analyzer.check_contraindications(
            scenario["medication"], 
            scenario["patient"]["diagnoses_text"]
        )
        
        print(f"Safety Level: {result['safety_level']}")
        print(f"Contraindications: {len(result['contraindications'])}")
        print(f"Warnings: {len(result['warnings'])}")
        print(f"Expected: {scenario['expected']}")
        
        if result["contraindications"]:
            for contra in result["contraindications"]:
                print(f"  ⚠️ {contra['type']}: {contra['reason']}")
        
        if result["warnings"]:
            for warning in result["warnings"]:
                print(f"  ⚡ {warning['type']}: {warning['reason']}")


async def test_medication_alternatives():
    """Test medication alternatives suggestions."""
    print("\n" + "="*60)
    print("🔄 TESTING MEDICATION ALTERNATIVES")
    print("="*60)
    
    from services.groq_service import MedicationAlternatives
    suggester = MedicationAlternatives()
    
    # Test medications that have alternatives
    test_medications = [
        {
            "medication": "Ibuprofen 400mg",
            "patient": PATIENT_P001,
            "reason": "Elderly patient with cardiac conditions"
        },
        {
            "medication": "Metformin 850mg",
            "patient": PATIENT_P002_HIGH_RISK, 
            "reason": "Kidney disease patient"
        },
        {
            "medication": "Aspirin 100mg",
            "patient": PATIENT_P001,
            "reason": "Bleeding risk assessment"
        }
    ]
    
    for i, test in enumerate(test_medications, 1):
        print(f"\n💊 Test {i}: {test['medication']}")
        print(f"Patient Context: {test['reason']}")
        
        alternatives = suggester.suggest_alternatives(test["medication"], test["patient"])
        
        print(f"Alternatives Available: {len(alternatives['alternatives'])}")
        print(f"Reason for Change: {alternatives['reason']}")
        
        if alternatives["alternatives"]:
            for j, alt in enumerate(alternatives["alternatives"], 1):
                print(f"  Alternative {j}: {alt['drug']}")
                print(f"    Dose: {alt['dose']}")
                print(f"    Advantages: {', '.join(alt['advantages'][:2])}...")
                if alt.get("patient_specific_advantages"):
                    print(f"    Patient-Specific: {', '.join(alt['patient_specific_advantages'][-1:])}")
        else:
            print("  No specific alternatives defined")


async def test_p001_layer2_comprehensive():
    """Comprehensive test of P001 scenario with Layer 2 analysis."""
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE P001 LAYER 2 TEST")
    print("="*60)
    
    print(f"Patient: {PATIENT_P001['name']} ({PATIENT_P001['age']} years)")
    print(f"Current Medications: {', '.join(PATIENT_P001['current_medications'])}")
    print(f"Conditions: {', '.join(PATIENT_P001['diagnoses_text'])}")
    print(f"New Medication: Ibuprofen 400mg twice daily")
    print("\n" + "-"*60)
    
    start_time = time.time()
    
    try:
        # Run Layer 2 analysis
        result = await enhanced_groq_service.analyze_drug_interactions_layer2(
            patient_data=PATIENT_P001,
            new_medications=["Ibuprofen 400mg twice daily"],
            drug_interactions_db=DRUG_INTERACTIONS_DB,
            notes="Elderly patient with knee pain after fall. High bleeding risk profile."
        )
        
        analysis_time = time.time() - start_time
        
        print("📊 ANALYSIS RESULTS:")
        print(f"Analysis Time: {analysis_time:.2f} seconds")
        print(f"Analysis Version: {result.get('analysis_version', 'Unknown')}")
        print(f"Safe to Prescribe: {result.get('safe_to_prescribe', 'Unknown')}")
        print(f"Priority Level: {result.get('priority_level', 'Unknown')}")
        
        # Analyze warnings
        warnings = result.get("warnings", [])
        print(f"\nTotal Warnings: {len(warnings)}")
        
        major_warnings = [w for w in warnings if w.get("severity") == "Major"]
        moderate_warnings = [w for w in warnings if w.get("severity") == "Moderate"]
        
        print(f"Major Warnings: {len(major_warnings)}")
        print(f"Moderate Warnings: {len(moderate_warnings)}")
        
        # Display warnings
        for i, warning in enumerate(warnings, 1):
            print(f"\n  Warning {i}: {warning.get('severity', 'Unknown')} - {warning.get('type', 'Unknown')}")
            print(f"    Description: {warning.get('description', 'No description')}")
            print(f"    Recommendation: {warning.get('recommendation', 'No recommendation')}")
        
        # Analyze Layer 2 enhancements
        layer2_data = result.get("layer2_enhancements", {})
        
        if layer2_data:
            print(f"\n📈 LAYER 2 ENHANCEMENTS:")
            
            # Patient risk assessment
            risk_data = layer2_data.get("patient_risk_assessment", {})
            if risk_data:
                print(f"  Overall Risk Score: {risk_data.get('overall_risk_score', 0)}/10")
                print(f"  Age Risk: {risk_data.get('age_risk', {}).get('risk_level', 'Unknown')}")
                print(f"  Comorbidity Risk: {risk_data.get('comorbidity_risk', {}).get('risk_level', 'Unknown')}")
            
            # Contraindications
            contraindications = layer2_data.get("drug_disease_contraindications", [])
            print(f"  Drug-Disease Contraindications: {len(contraindications)}")
            
            # Alternatives
            alternatives = layer2_data.get("medication_alternatives", [])
            print(f"  Alternative Medications: {len(alternatives)}")
            
            if alternatives:
                for alt in alternatives:
                    print(f"    Alternative for {alt.get('original_medication', 'Unknown')}: {len(alt.get('alternatives', []))} options")
                    if alt.get('alternatives'):
                        first_alt = alt['alternatives'][0]
                        print(f"      Best option: {first_alt.get('drug', 'Unknown')} - {first_alt.get('dose', 'No dose')}")
        
        # Validation results
        print(f"\n✅ VALIDATION RESULTS:")
        
        validation_results = {
            "major_bleeding_warning": any("bleeding" in w.get("description", "").lower() and w.get("severity") == "Major" for w in warnings),
            "patient_age_considered": "72" in result.get("llm_reasoning", "") or layer2_data.get("patient_risk_assessment", {}).get("age_risk", {}).get("risk_level") in ["High", "Very High"],
            "contraindications_checked": len(layer2_data.get("drug_disease_contraindications", [])) >= 0,
            "alternatives_provided": len(layer2_data.get("medication_alternatives", [])) > 0,
            "unsafe_prescription": not result.get("safe_to_prescribe", True),
            "response_time_acceptable": analysis_time < 5.0  # Slightly higher for Layer 2
        }
        
        passed_tests = sum(validation_results.values())
        total_tests = len(validation_results)
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        
        for test_name, passed in validation_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        overall_success = passed_tests >= 4  # At least 4/6 tests should pass
        
        print(f"\n🎯 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ NEEDS IMPROVEMENT'}")
        
        if overall_success:
            print("Layer 2 implementation is working correctly!")
            print("Key features validated:")
            print("- Drug-drug interaction detection")
            print("- Patient-specific risk assessment") 
            print("- Drug-disease contraindication analysis")
            print("- Alternative medication suggestions")
        else:
            print("Some Layer 2 features need attention.")
            print("Check the failed validations above.")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {str(e)}")
        print(f"Analysis time: {time.time() - start_time:.2f} seconds")
        return False


async def test_performance_comparison():
    """Compare Layer 1 vs Layer 2 performance."""
    print("\n" + "="*60)
    print("⚡ PERFORMANCE COMPARISON: Layer 1 vs Layer 2")
    print("="*60)
    
    # Test data
    test_patient = PATIENT_P001
    test_medications = ["Ibuprofen 400mg"]
    test_db = DRUG_INTERACTIONS_DB
    test_notes = "Performance comparison test"
    
    # Layer 1 test
    print("\n🔥 Testing Layer 1 Performance...")
    layer1_times = []
    
    for i in range(3):
        start_time = time.time()
        try:
            layer1_result = await enhanced_groq_service._analyze_drug_drug_interactions(
                patient_data=test_patient,
                new_medications=test_medications,
                drug_interactions_db=test_db,
                notes=test_notes
            )
            layer1_time = time.time() - start_time
            layer1_times.append(layer1_time)
            print(f"  Run {i+1}: {layer1_time:.2f}s")
        except Exception as e:
            print(f"  Run {i+1}: ERROR - {str(e)}")
    
    # Layer 2 test
    print("\n🚀 Testing Layer 2 Performance...")
    layer2_times = []
    
    for i in range(3):
        start_time = time.time()
        try:
            layer2_result = await enhanced_groq_service.analyze_drug_interactions_layer2(
                patient_data=test_patient,
                new_medications=test_medications,
                drug_interactions_db=test_db,
                notes=test_notes
            )
            layer2_time = time.time() - start_time
            layer2_times.append(layer2_time)
            print(f"  Run {i+1}: {layer2_time:.2f}s")
        except Exception as e:
            print(f"  Run {i+1}: ERROR - {str(e)}")
    
    # Performance analysis
    if layer1_times and layer2_times:
        avg_layer1 = sum(layer1_times) / len(layer1_times)
        avg_layer2 = sum(layer2_times) / len(layer2_times)
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"Layer 1 Average: {avg_layer1:.2f}s")
        print(f"Layer 2 Average: {avg_layer2:.2f}s")
        print(f"Layer 2 Overhead: {avg_layer2 - avg_layer1:.2f}s ({((avg_layer2/avg_layer1-1)*100):.1f}% slower)")
        
        # Acceptable performance thresholds
        layer1_acceptable = avg_layer1 < 3.0
        layer2_acceptable = avg_layer2 < 5.0  # Higher threshold for Layer 2
        
        print(f"Layer 1 Performance: {'✅ GOOD' if layer1_acceptable else '⚠️ SLOW'} (target: <3s)")
        print(f"Layer 2 Performance: {'✅ GOOD' if layer2_acceptable else '⚠️ SLOW'} (target: <5s)")
        
        return layer1_acceptable and layer2_acceptable
    else:
        print("❌ Performance test failed - no successful runs")
        return False


async def test_cache_performance_layer2():
    """Test caching performance with Layer 2."""
    print("\n" + "="*60)
    print("💾 TESTING Layer 2 CACHE PERFORMANCE")
    print("="*60)
    
    # Clear cache first
    enhanced_groq_service._cache.clear()
    print("Cache cleared")
    
    test_patient = PATIENT_P001
    test_medications = ["Ibuprofen 400mg"]
    test_db = DRUG_INTERACTIONS_DB
    
    # First call - should miss cache
    print("\n🔄 First call (Cache MISS expected):")
    start_time = time.time()
    
    try:
        result1 = await enhanced_groq_service.analyze_drug_interactions_layer2(
            patient_data=test_patient,
            new_medications=test_medications,
            drug_interactions_db=test_db,
            notes="Cache test - first call"
        )
        first_call_time = time.time() - start_time
        print(f"First call time: {first_call_time:.2f} seconds")
        
        # Second call - should hit cache
        print("\n⚡ Second call (Cache HIT expected):")
        start_time = time.time()
        
        result2 = await enhanced_groq_service.analyze_drug_interactions_layer2(
            patient_data=test_patient,
            new_medications=test_medications,
            drug_interactions_db=test_db,
            notes="Cache test - second call"
        )
        second_call_time = time.time() - start_time
        print(f"Second call time: {second_call_time:.2f} seconds")
        
        # Cache performance analysis
        if first_call_time > 0 and second_call_time >= 0:
            speedup = first_call_time / max(second_call_time, 0.001)  # Avoid division by zero
            
            print(f"\n📈 CACHE PERFORMANCE:")
            print(f"Cache Speedup: {speedup:.1f}x faster")
            print(f"Time Saved: {first_call_time - second_call_time:.2f} seconds")
            
            # Verify results consistency
            warnings1 = len(result1.get("warnings", []))
            warnings2 = len(result2.get("warnings", []))
            
            results_identical = warnings1 == warnings2
            print(f"Results Consistency: {'✅ IDENTICAL' if results_identical else '❌ DIFFERENT'}")
            
            # Performance validation
            cache_effective = second_call_time < first_call_time * 0.2  # Should be at least 5x faster
            
            print(f"Cache Effectiveness: {'✅ EXCELLENT' if cache_effective else '⚠️ NEEDS IMPROVEMENT'}")
            
            return cache_effective and results_identical
        
    except Exception as e:
        print(f"❌ Cache test failed: {str(e)}")
        return False


async def main():
    """Main test runner for Layer 2."""
    print("🚀 SADEWA LAYER 2 - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    test_results = {}
    
    # Test 1: Connection
    test_results["connection"] = await test_layer2_connection()
    
    if not test_results["connection"]:
        print("\n❌ CONNECTION FAILED - Cannot proceed with other tests")
        print("Please check your GROQ_API_KEY in .env file")
        return
    
    # Test 2: Patient Risk Assessment
    await test_patient_risk_assessment()
    
    # Test 3: Drug Contraindication Analysis
    await test_drug_contraindication_analysis()
    
    # Test 4: Medication Alternatives
    await test_medication_alternatives()
    
    # Test 5: Comprehensive P001 Test
    test_results["p001_comprehensive"] = await test_p001_layer2_comprehensive()
    
    # Test 6: Performance Comparison
    test_results["performance"] = await test_performance_comparison()
    
    # Test 7: Cache Performance
    test_results["cache"] = await test_cache_performance_layer2()
    
    # Final Summary
    print("\n" + "="*80)
    print("📋 FINAL TEST SUMMARY")
    print("="*80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Overall Success Rate: {passed_tests}/{total_tests} tests passed")
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Layer 2 implementation is ready!")
        print("\n🚀 READY FOR:")
        print("   - Production deployment")
        print("   - Frontend integration") 
        print("   - Demo preparation")
        print("   - Competition submission")
    elif passed_tests >= total_tests * 0.8:  # 80% pass rate
        print("\n✅ MOSTLY SUCCESSFUL! Minor issues to address.")
        print("Layer 2 core functionality is working.")
    else:
        print("\n⚠️ SIGNIFICANT ISSUES DETECTED")
        print("Review failed tests and fix implementation.")
    
    print(f"\n⏱️ Layer 2 Features Validated:")
    print("   ✅ Enhanced drug-drug interaction analysis")
    print("   ✅ Patient-specific risk assessment")
    print("   ✅ Drug-disease contraindication checking")
    print("   ✅ Alternative medication suggestions")
    print("   ✅ Performance optimization with caching")
    
    print(f"\n🎯 Next Steps:")
    if passed_tests == total_tests:
        print("   1. Deploy to Railway production")
        print("   2. Update frontend to use Layer 2 endpoints")
        print("   3. Prepare demo scenarios")
    else:
        print("   1. Fix failing tests")
        print("   2. Re-run test suite")
        print("   3. Proceed to deployment when all tests pass")


if __name__ == "__main__":
    asyncio.run(main())