#!/usr/bin/env python3
"""
Test script untuk Day 1 - Basic functionality testing
"""
import asyncio
import aiohttp # json dihapus karena tidak digunakan

BASE_URL = "http://localhost:8000"

async def test_endpoints():
    """Menjalankan serangkaian tes terhadap endpoint API SADEWA."""
    async with aiohttp.ClientSession() as session:

        print("🧪 Testing SADEWA Backend - Day 1")
        print("=" * 50)

        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                data = await response.json()
                print(f"   ✅ Status: {response.status}")
                print(f"   📋 Response: {data}")
        # Mengganti Exception umum dengan yang lebih spesifik
        except aiohttp.ClientError as e:
            print(f"   ❌ Error: {e}")

        # Test 2: Get All Patients
        print("\n2. Testing Get All Patients...")
        try:
            async with session.get(f"{BASE_URL}/api/patients") as response:
                data = await response.json()
                print(f"   ✅ Status: {response.status}")
                print(f"   👥 Found {len(data)} patients")
                print(f"   📋 First patient: {data[0]['name'] if data else 'None'}")
        except aiohttp.ClientError as e:
            print(f"   ❌ Error: {e}")

        # Test 3: Get Specific Patient
        print("\n3. Testing Get Patient P001...")
        try:
            async with session.get(f"{BASE_URL}/api/patients/P001") as response:
                data = await response.json()
                print(f"   ✅ Status: {response.status}")
                print(f"   👤 Patient: {data.get('name', 'Unknown')}")
                print(f"   💊 Medications: {len(data.get('current_medications', []))}")
        except aiohttp.ClientError as e:
            print(f"   ❌ Error: {e}")

        # Test 4: ICD-10 Search
        print("\n4. Testing ICD-10 Search...")
        try:
            params = {"q": "diabetes", "limit": 3}
            async with session.get(f"{BASE_URL}/api/icd10/search", params=params) as response:
                data = await response.json()
                print(f"   ✅ Status: {response.status}")
                print(f"   🔍 Found {len(data)} results for 'diabetes'")
                if data:
                    print(f"   📋 First result: {data[0]['code']} - {data[0]['name_id']}")
        except aiohttp.ClientError as e:
            print(f"   ❌ Error: {e}")

        # Test 5: Groq Connection Test
        print("\n5. Testing Groq Connection...")
        try:
            async with session.get(f"{BASE_URL}/api/test-groq") as response:
                data = await response.json()
                print(f"   ✅ Status: {response.status}")
                print(f"   🤖 Groq Response: {data.get('response', 'No response')}")
        except aiohttp.ClientError as e:
            print(f"   ❌ Error: {e}")

        # Test 6: Basic Interaction Analysis
        print("\n6. Testing Basic Interaction Analysis...")
        try:
            payload = {
                "patient_id": "P001",
                "new_medications": ["Ibuprofen 400mg"],
                "notes": "Patient complains of knee pain"
            }
            async with session.post(
                f"{BASE_URL}/api/analyze-interactions",
                json=payload
            ) as response:
                data = await response.json()
                print(f"   ✅ Status: {response.status}")
                print(f"   ⚠️  Warnings found: {len(data.get('warnings', []))}")
                print(f"   ✅ Safe to prescribe: {data.get('safe_to_prescribe', False)}")
                if data.get('warnings'):
                    for warning in data['warnings']:
                        print(f"      - {warning['severity']}: {warning['description']}")
        except aiohttp.ClientError as e:
            print(f"   ❌ Error: {e}")

        print("\n" + "=" * 50)
        print("🎯 Day 1 Testing Complete!")

if __name__ == "__main__":
    print("Make sure your FastAPI server is running (uvicorn main:app --reload)")
    asyncio.run(test_endpoints())
    