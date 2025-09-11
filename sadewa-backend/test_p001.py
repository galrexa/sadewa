#!/usr/bin/env python3
"""
Test Case DAY 2: Patient P001 + Ibuprofen
Expected: MAJOR bleeding risk warning (Warfarin + Ibuprofen interaction)
"""
import asyncio
import json
from datetime import datetime

import aiohttp

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_PATIENT_ID = "P001"
NEW_MEDICATION = ["Ibuprofen 400mg TID (for knee pain)"]
CLINICAL_NOTES = "Patient complains of severe knee pain, requests pain medication. Has history of AF on warfarin."

async def test_p001_ibuprofen_interaction():
    """Test case utama untuk Patient P001 + Ibuprofen interaction"""
    print("🧪 SADEWA DAY 2 - Enhanced Drug Interaction Analysis")
    print("=" * 60)
    print(f"Test Case: Patient {TEST_PATIENT_ID} + Ibuprofen 400mg")
    print("Expected: MAJOR bleeding risk warning")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # Step 1: Verify patient data
        print("\n📋 Step 1: Verify Patient Data")
        try:
            async with session.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}") as response:
                if response.status == 200:
                    patient_data = await response.json()
                    print(f"   ✅ Patient: {patient_data.get('name', 'Unknown')}")
                    print(f"   📅 Age: {patient_data.get('age')} years")
                    print(f"   ⚖️ Weight: {patient_data.get('weight_kg', 'Unknown')} kg")
                    print("   💊 Current Medications:")
                    for med in patient_data.get('current_medications', []):
                        print(f"      - {med}")
                    print("   🏥 Diagnoses:")
                    for diag in patient_data.get('diagnoses_text', []):
                        print(f"      - {diag}")
                else:
                    print(f"   ❌ Failed to get patient data: {response.status}")
                    return
        except aiohttp.ClientError as e:
            print(f"   ❌ Error getting patient: {e}")
            return

        # Step 2: Test enhanced Groq connection
        print("\n🤖 Step 2: Test Enhanced Groq Connection")
        try:
            async with session.get(f"{BASE_URL}/api/test-groq") as response:
                if response.status == 200:
                    groq_data = await response.json()
                    print(f"   ✅ Groq Status: {groq_data.get('status')}")
                    print(f"   🔗 Response: {groq_data.get('response')}")
                else:
                    print(f"   ❌ Groq connection failed: {response.status}")
        except aiohttp.ClientError as e:
            print(f"   ❌ Error testing Groq: {e}")

        # Step 3: Main interaction analysis
        print("\n⚕️ Step 3: Analyze Drug Interactions")
        print(f"   New Medication: {NEW_MEDICATION[0]}")
        print(f"   Clinical Notes: {CLINICAL_NOTES}")

        request_payload = {
            "patient_id": TEST_PATIENT_ID,
            "new_medications": NEW_MEDICATION,
            "notes": CLINICAL_NOTES
        }

        start_time = datetime.now()

        try:
            async with session.post(
                f"{BASE_URL}/api/analyze-interactions",
                json=request_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()

                print(f"   ⏱️ Response Time: {response_time:.2f} seconds")

                if response.status == 200:
                    analysis_result = await response.json()

                    # Display results
                    print("\n📊 ANALYSIS RESULTS:")
                    print(f"   Overall Risk Level: {analysis_result.get('overall_risk_level')}")
                    print(f"   Safe to Prescribe: {analysis_result.get('safe_to_prescribe')}")
                    print(f"   Confidence Score: {analysis_result.get('confidence_score', 'N/A')}")

                    # Display warnings
                    warnings = analysis_result.get('warnings', [])
                    print(f"\n⚠️ WARNINGS ({len(warnings)} found):")

                    major_warnings = 0
                    for i, warning in enumerate(warnings, 1):
                        severity = warning.get('severity', 'UNKNOWN')
                        if severity == 'MAJOR':
                            major_warnings += 1

                        print(f"\n   Warning {i}: {severity}")
                        print(f"   Type: {warning.get('type', 'UNKNOWN')}")
                        print(f"   Drugs: {', '.join(warning.get('drugs_involved', []))}")
                        print(f"   Description: {warning.get('description', 'N/A')}")
                        print(f"   Clinical Impact: {warning.get('clinical_significance', 'N/A')}")
                        print(f"   Recommendation: {warning.get('recommendation', 'N/A')}")
                        print(f"   Monitoring: {warning.get('monitoring_required', 'N/A')}")

                    # Display contraindications if any
                    contraindications = analysis_result.get('contraindications', [])
                    if contraindications:
                        print(f"\n🚫 CONTRAINDICATIONS ({len(contraindications)} found):")
                        for contra in contraindications:
                            print(f"   - {contra.get('drug')} vs {contra.get('diagnosis')}")
                            print(f"     Reason: {contra.get('reason')}")

                    # Display dosing adjustments if any
                    dosing_adjustments = analysis_result.get('dosing_adjustments', [])
                    if dosing_adjustments:
                        print(f"\n💊 DOSING ADJUSTMENTS ({len(dosing_adjustments)} found):")
                        for adjustment in dosing_adjustments:
                            print(f"   - {adjustment.get('drug')}")
                            print(f"     Standard: {adjustment.get('standard_dose')}")
                            print(f"     Recommended: {adjustment.get('recommended_dose')}")
                            print(f"     Reason: {adjustment.get('reason')}")

                    # Display monitoring plan
                    monitoring = analysis_result.get('monitoring_plan', [])
                    if monitoring:
                        print("\n🔍 MONITORING PLAN:")
                        for item in monitoring:
                            print(f"   - {item}")

                    # Display AI reasoning
                    reasoning = analysis_result.get('llm_reasoning', '')
                    if reasoning:
                        print("\n🧠 AI REASONING:")
                        print(f"   {reasoning}")

                    # Test validation
                    print("\n✅ TEST VALIDATION:")
                    print("Expected: MAJOR bleeding risk warning")
                    print(f"   Actual: {analysis_result.get('overall_risk_level')} risk level")
                    print(f"   Major warnings found: {major_warnings}")
                    print(f"   Response time: {response_time:.2f}s (target: <3s)")

                    # Success criteria check
                    success_criteria = [
                        ("Major risk detected", analysis_result.get('overall_risk_level') == 'MAJOR'),
                        ("Major warnings present", major_warnings > 0),
                        ("Not safe to prescribe", not analysis_result.get('safe_to_prescribe', True)),
                        ("Response time OK", response_time < 3.0),
                        ("Warfarin mentioned", any('warfarin' in str(w).lower() for w in warnings)),
                        ("Bleeding risk mentioned",
                         any('bleeding' in str(w).lower() or 'hemorrhag' in str(w).lower() for w in warnings))
                    ]

                    print("\n🎯 SUCCESS CRITERIA:")
                    all_passed = True
                    for criterion, passed in success_criteria:
                        status = "✅ PASS" if passed else "❌ FAIL"
                        print(f"   {criterion}: {status}")
                        if not passed:
                            all_passed = False

                    if all_passed:
                        print("\n🏆 TEST PASSED: All success criteria met!")
                    else:
                        print("\n⚠️ TEST PARTIAL: Some criteria not met, but analysis completed")

                    # Save results for debugging
                    with open(f'test_results_p001_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                              'w',
                              encoding='utf-8') as f:
                        json.dump(analysis_result, f, indent=2, ensure_ascii=False)

                else:
                    error_text = await response.text()
                    print(f"   ❌ Analysis failed: {response.status}")
                    print(f"   Error: {error_text}")

        except aiohttp.ClientError as e:
            print(f"   ❌ Error during analysis: {e}")

async def test_additional_scenarios():
    """Test skenario tambahan untuk validasi"""
    print("\n" + "=" * 60)
    print("🧪 ADDITIONAL TEST SCENARIOS")
    print("=" * 60)

    test_cases = [
        {
            "patient_id": "P002",
            "new_medications": ["Aspirin 100mg OD"],
            "notes": "Secondary prevention post-MI",
            "expected_risk": "MODERATE",
            "description": "Test aspirin interaction"
        },
        {
            "patient_id": "P001",
            "new_medications": ["Paracetamol 500mg QID"],
            "notes": "Safe alternative for pain management",
            "expected_risk": "LOW",
            "description": "Test safe alternative"
        }
    ]

    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {test_case['description']}")
            print(f"   Patient: {test_case['patient_id']}")
            print(f"   Medication: {test_case['new_medications'][0]}")
            print(f"   Expected Risk: {test_case['expected_risk']}")

            try:
                async with session.post(
                    f"{BASE_URL}/api/analyze-interactions",
                    json={
                        "patient_id": test_case["patient_id"],
                        "new_medications": test_case["new_medications"],
                        "notes": test_case["notes"]
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        actual_risk = result.get('overall_risk_level')
                        safe_to_prescribe = result.get('safe_to_prescribe')

                        print(f"   ✅ Result: {actual_risk} risk, Safe: {safe_to_prescribe}")

                        if actual_risk == test_case['expected_risk']:
                            print("   🎯 Expected risk level matched!")
                        else:
                            print("   ⚠️ Risk level differs from expected")
                    else:
                        print(f"   ❌ Request failed: {response.status}")

            except aiohttp.ClientError as e:
                print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_p001_ibuprofen_interaction())
    asyncio.run(test_additional_scenarios())