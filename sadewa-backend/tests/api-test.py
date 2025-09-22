# api_testing_complete.py
"""
Comprehensive API Testing Suite for SADEWA
Run this script to test all optimized endpoints
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, date
from typing import Dict, Any, List
import sys

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your server URL
TIMEOUT = 30

class Colors:
    """Console colors for better output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.patient_ids = []  # Store created patient IDs for cleanup
        self.medical_record_ids = []  # Store created record IDs
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test(self, test_name: str, success: bool, response_data: Dict = None, error: str = None):
        """Log test results"""
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if success else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status} {test_name}")
        
        if error:
            print(f"   {Colors.RED}Error: {error}{Colors.END}")
        elif response_data:
            if 'processing_time_ms' in response_data:
                time_ms = response_data['processing_time_ms']
                time_color = Colors.GREEN if time_ms < 500 else Colors.YELLOW if time_ms < 1000 else Colors.RED
                print(f"   {time_color}⏱️  {time_ms:.2f}ms{Colors.END}")
            
            if 'total' in response_data:
                print(f"   📊 Total: {response_data['total']}")
            elif 'id' in response_data:
                print(f"   🆔 ID: {response_data['id']}")
        
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })

    async def test_health_endpoints(self):
        """Test system health and monitoring endpoints"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== TESTING HEALTH & MONITORING ==={Colors.END}")
        
        # Test root endpoint
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                data = await response.json()
                success = response.status == 200 and 'version' in data
                self.log_test("Root endpoint", success, data)
        except Exception as e:
            self.log_test("Root endpoint", False, error=str(e))
        
        # Test health check
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                success = response.status == 200 and data.get('status') in ['healthy', 'unhealthy']
                self.log_test("Health check", success, data)
        except Exception as e:
            self.log_test("Health check", False, error=str(e))
        
        # Test monitoring endpoint
        try:
            async with self.session.get(f"{self.base_url}/monitoring") as response:
                data = await response.json()
                success = response.status == 200 and 'performance_metrics' in data
                self.log_test("Monitoring dashboard", success, data)
        except Exception as e:
            self.log_test("Monitoring dashboard", False, error=str(e))

    async def test_patient_endpoints(self):
        """Test optimized patient endpoints"""
        print(f"\n{Colors.BOLD}{Colors.GREEN}=== TESTING PATIENT ENDPOINTS ==={Colors.END}")
        
        # Test patient registration
        patient_data = {
            "name": "John Doe Test",
            "age": 35,
            "gender": "male",
            "phone": "081234567890",
            "weight_kg": 70,
            "medical_history": ["Hipertensi", "Diabetes"],
            "allergies": ["Penisilin", "Aspirin"],
            "risk_factors": ["Merokok", "Kurang olahraga"]
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/patients/register",
                json=patient_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                data = await response.json()
                success = response.status == 201 and 'id' in data
                if success:
                    self.patient_ids.append(data['id'])
                self.log_test("Patient registration", success, data)
        except Exception as e:
            self.log_test("Patient registration", False, error=str(e))
        
        # Test patient search
        try:
            async with self.session.get(
                f"{self.base_url}/api/patients/search?q=John&gender=male&limit=10"
            ) as response:
                data = await response.json()
                success = response.status == 200 and 'patients' in data
                self.log_test("Patient search", success, data)
        except Exception as e:
            self.log_test("Patient search", False, error=str(e))
        
        # Test patient detail (if we have a patient ID)
        if self.patient_ids:
            patient_id = self.patient_ids[0]
            try:
                async with self.session.get(
                    f"{self.base_url}/api/patients/{patient_id}?include_timeline=true"
                ) as response:
                    data = await response.json()
                    success = response.status == 200 and data.get('id') == patient_id
                    self.log_test("Patient detail", success, data)
            except Exception as e:
                self.log_test("Patient detail", False, error=str(e))
        
        # Test patient statistics
        try:
            async with self.session.get(f"{self.base_url}/api/patients/stats/summary") as response:
                data = await response.json()
                success = response.status == 200 and 'total_patients' in data
                self.log_test("Patient statistics", success, data)
        except Exception as e:
            self.log_test("Patient statistics", False, error=str(e))

    async def test_medical_records_endpoints(self):
        """Test medical records endpoints"""
        print(f"\n{Colors.BOLD}{Colors.PURPLE}=== TESTING MEDICAL RECORDS ==={Colors.END}")
        
        if not self.patient_ids:
            print(f"{Colors.YELLOW}⚠️  Skipping medical records tests - no patient ID available{Colors.END}")
            return
        
        patient_id = self.patient_ids[0]
        
        # Test create medical record
        record_data = {
            "patient_id": patient_id,
            "visit_type": "initial",
            "chief_complaint": "Demam dan batuk sejak 3 hari",
            "symptoms": [
                {
                    "symptom": "Demam",
                    "severity": "moderate",
                    "duration": "acute",
                    "description": "Demam tinggi hingga 39°C",
                    "onset_date": "2024-01-20"
                },
                {
                    "symptom": "Batuk",
                    "severity": "mild",
                    "duration": "acute",
                    "description": "Batuk kering tidak berdahak"
                }
            ],
            "vital_signs": {
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "heart_rate": 88,
                "temperature": 38.5,
                "respiratory_rate": 20,
                "oxygen_saturation": 98
            },
            "diagnosis_code": "J00",
            "diagnosis_text": "Common cold",
            "medications": ["Paracetamol", "Vitamin C"],
            "treatment_plan": "Istirahat, minum air putih, konsumsi obat sesuai dosis",
            "notes": "Pasien dalam kondisi stabil, dianjurkan kontrol 3 hari"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/medical-records",
                json=record_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                data = await response.json()
                success = response.status == 201 and 'id' in data
                if success:
                    self.medical_record_ids.append(data['id'])
                self.log_test("Create medical record", success, data)
        except Exception as e:
            self.log_test("Create medical record", False, error=str(e))
        
        # Test get patient medical history
        try:
            async with self.session.get(
                f"{self.base_url}/api/medical-records/patient/{patient_id}?limit=5&include_allergies=true"
            ) as response:
                data = await response.json()
                success = response.status == 200 and 'medical_records' in data
                self.log_test("Patient medical history", success, data)
        except Exception as e:
            self.log_test("Patient medical history", False, error=str(e))
        
        # Test search by symptoms
        try:
            async with self.session.get(
                f"{self.base_url}/api/medical-records/search/symptoms?symptoms=demam,batuk&limit=5"
            ) as response:
                data = await response.json()
                success = response.status == 200 and 'medical_records' in data
                self.log_test("Search by symptoms", success, data)
        except Exception as e:
            self.log_test("Search by symptoms", False, error=str(e))
        
        # Test medical records statistics
        try:
            async with self.session.get(
                f"{self.base_url}/api/medical-records/stats/summary?days=30"
            ) as response:
                data = await response.json()
                success = response.status == 200 and 'total_records' in data
                self.log_test("Medical records statistics", success, data)
        except Exception as e:
            self.log_test("Medical records statistics", False, error=str(e))

    async def test_ai_diagnosis_endpoints(self):
        """Test AI diagnosis and drug interaction endpoints"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== TESTING AI DIAGNOSIS & DRUG INTERACTIONS ==={Colors.END}")
        
        # Test drug interaction analysis
        interaction_data = {
            "medications": ["Warfarin", "Aspirin", "Ibuprofen"],
            "patient_id": self.patient_ids[0] if self.patient_ids else None,
            "include_cache": True
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/analyze/drug-interactions",
                json=interaction_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                data = await response.json()
                success = response.status == 200 and 'total_interactions' in data
                self.log_test("Drug interaction analysis", success, data)
        except Exception as e:
            self.log_test("Drug interaction analysis", False, error=str(e))
        
        # Test AI diagnosis analysis (if we have patient ID)
        if self.patient_ids:
            ai_diagnosis_data = {
                "patient_id": self.patient_ids[0],
                "analysis_type": "diagnosis",
                "symptoms": ["Demam", "Batuk", "Sakit kepala"],
                "chief_complaint": "Demam dan batuk sejak 3 hari",
                "vital_signs": {
                    "temperature": 38.5,
                    "heart_rate": 88,
                    "blood_pressure_systolic": 120,
                    "blood_pressure_diastolic": 80
                },
                "current_medications": ["Paracetamol"],
                "allergies": ["Penisilin"],
                "age": 35,
                "gender": "male"
            }
            
            try:
                async with self.session.post(
                    f"{self.base_url}/api/analyze/ai-diagnosis",
                    json=ai_diagnosis_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    data = await response.json()
                    success = response.status == 200 and 'confidence_score' in data
                    self.log_test("AI diagnosis analysis", success, data)
            except Exception as e:
                self.log_test("AI diagnosis analysis", False, error=str(e))
        
        # Test AI analysis statistics
        try:
            async with self.session.get(
                f"{self.base_url}/api/analyze/stats/summary?days=30"
            ) as response:
                data = await response.json()
                success = response.status == 200 and 'analysis_statistics' in data
                self.log_test("AI analysis statistics", success, data)
        except Exception as e:
            self.log_test("AI analysis statistics", False, error=str(e))

    async def test_system_endpoints(self):
        """Test system management endpoints"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}=== TESTING SYSTEM ENDPOINTS ==={Colors.END}")
        
        # Test cache statistics
        try:
            async with self.session.get(f"{self.base_url}/api/system/cache-stats") as response:
                data = await response.json()
                success = response.status == 200 and 'cache_statistics' in data
                self.log_test("Cache statistics", success, data)
        except Exception as e:
            self.log_test("Cache statistics", False, error=str(e))
        
        # Test cache clear (admin function)
        try:
            async with self.session.post(f"{self.base_url}/api/system/clear-cache") as response:
                data = await response.json()
                success = response.status == 200 and 'message' in data
                self.log_test("Clear cache", success, data)
        except Exception as e:
            self.log_test("Clear cache", False, error=str(e))

    async def test_existing_endpoints(self):
        """Test existing endpoints for compatibility"""
        print(f"\n{Colors.BOLD}{Colors.WHITE}=== TESTING EXISTING ENDPOINTS ==={Colors.END}")
        
        # Test drug search
        try:
            async with self.session.get(f"{self.base_url}/api/drugs/search?q=paracetamol&limit=5") as response:
                data = await response.json()
                success = response.status == 200
                self.log_test("Drug search", success, data)
        except Exception as e:
            self.log_test("Drug search", False, error=str(e))
        
        # Test ICD-10 search
        try:
            async with self.session.get(f"{self.base_url}/api/icd10/search?q=fever&limit=5") as response:
                data = await response.json()
                success = response.status == 200
                self.log_test("ICD-10 search", success, data)
        except Exception as e:
            self.log_test("ICD-10 search", False, error=str(e))

    async def cleanup_test_data(self):
        """Clean up test data"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}=== CLEANING UP TEST DATA ==={Colors.END}")
        
        # Delete created medical records
        for record_id in self.medical_record_ids:
            try:
                # Note: You might need to implement delete endpoints
                print(f"📝 Would delete medical record {record_id}")
            except Exception as e:
                print(f"❌ Failed to delete medical record {record_id}: {e}")
        
        # Delete created patients
        for patient_id in self.patient_ids:
            try:
                # Note: You might need to implement delete endpoints
                print(f"👤 Would delete patient {patient_id}")
            except Exception as e:
                print(f"❌ Failed to delete patient {patient_id}: {e}")

    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n{Colors.BOLD}{'='*50}")
        print(f"           TEST SUMMARY")
        print(f"{'='*50}{Colors.END}")
        print(f"Total Tests: {total_tests}")
        print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed_tests}{Colors.END}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        if failed_tests > 0:
            print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test_name']}: {result['error']}")

    async def run_all_tests(self):
        """Run all test suites"""
        print(f"{Colors.BOLD}{Colors.BLUE}🧪 Starting SADEWA API Testing Suite{Colors.END}")
        print(f"🌐 Testing server: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        
        try:
            await self.test_health_endpoints()
            await self.test_patient_endpoints()
            await self.test_medical_records_endpoints()
            await self.test_ai_diagnosis_endpoints()
            await self.test_system_endpoints()
            await self.test_existing_endpoints()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⚠️  Testing interrupted by user{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Unexpected error during testing: {e}{Colors.END}")
        finally:
            await self.cleanup_test_data()
            
            total_time = time.time() - start_time
            print(f"\n⏱️  Total testing time: {total_time:.2f} seconds")
            self.print_summary()

async def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    async with APITester(base_url) as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())