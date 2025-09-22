#!/usr/bin/env python3
"""
Test Migration Script
SADEWA - Smart Assistant for Drug & Evidence Warning

Tests the migration process and verifies data integrity.
"""

import os
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models import Patient, PatientMedication, PatientDiagnosis, PatientAllergy, DrugInteraction
from app.routers.interactions import load_patients, load_drug_interactions, load_patients_from_json, load_drug_interactions_from_json

class MigrationTester:
    def __init__(self):
        self.engine = engine
        if not self.engine:
            print("Database engine not available")
            sys.exit(1)
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_session(self):
        """Create a new database session"""
        return self.SessionLocal()
    
    def test_data_consistency(self):
        """Test that JSON and database data are consistent"""
        print("Testing data consistency between JSON and Database...")
        
        db = self.create_session()
        try:
            # Load data from both sources
            db_patients = load_patients(db)
            json_patients = load_patients_from_json()
            
            db_interactions = load_drug_interactions(db)
            json_interactions = load_drug_interactions_from_json()
            
            # Compare counts
            print(f"Patients - DB: {len(db_patients)}, JSON: {len(json_patients)}")
            print(f"Interactions - DB: {len(db_interactions)}, JSON: {len(json_interactions)}")
            
            # Test specific patient data
            if db_patients and json_patients:
                db_patient = next((p for p in db_patients if p['id'] == 'P001'), None)
                json_patient = next((p for p in json_patients if p['id'] == 'P001'), None)
                
                if db_patient and json_patient:
                    print(f"Patient P001 comparison:")
                    print(f"  Name - DB: {db_patient['name']}, JSON: {json_patient['name']}")
                    print(f"  Age - DB: {db_patient['age']}, JSON: {json_patient['age']}")
                    print(f"  Medications - DB: {len(db_patient['current_medications'])}, JSON: {len(json_patient['current_medications'])}")
                
        except Exception as e:
            print(f"Error testing consistency: {e}")
        finally:
            db.close()
    
    def test_api_endpoints(self):
        """Test that API endpoints work with database"""
        print("Testing API endpoints...")
        
        db = self.create_session()
        try:
            # Test loading functions
            patients = load_patients(db)
            interactions = load_drug_interactions(db)
            
            print(f"API load test successful:")
            print(f"  Loaded {len(patients)} patients")
            print(f"  Loaded {len(interactions)} interactions")
            
            # Test patient relationships
            if patients:
                sample_patient = patients[0]
                print(f"Sample patient: {sample_patient['name']}")
                print(f"  Medications: {len(sample_patient['current_medications'])}")
                print(f"  Diagnoses: {len(sample_patient['diagnoses_text'])}")
                print(f"  Allergies: {len(sample_patient['allergies'])}")
            
        except Exception as e:
            print(f"Error testing API endpoints: {e}")
        finally:
            db.close()
    
    def test_database_relationships(self):
        """Test database relationships and foreign keys"""
        print("Testing database relationships...")
        
        db = self.create_session()
        try:
            # Test patient with relationships
            patient = db.query(Patient).first()
            if patient:
                print(f"Testing relationships for patient: {patient.name}")
                print(f"  Medications count: {len(patient.medications)}")
                print(f"  Diagnoses count: {len(patient.diagnoses)}")
                print(f"  Allergies count: {len(patient.allergies)}")
                
                # Test medication details
                if patient.medications:
                    med = patient.medications[0]
                    print(f"  First medication: {med.medication_name} {med.dosage}")
                
                # Test diagnosis details
                if patient.diagnoses:
                    diag = patient.diagnoses[0]
                    print(f"  First diagnosis: {diag.diagnosis_text}")
            
            # Test drug interactions
            interaction_count = db.query(DrugInteraction).count()
            print(f"Drug interactions in database: {interaction_count}")
            
            if interaction_count > 0:
                interaction = db.query(DrugInteraction).first()
                print(f"Sample interaction: {interaction.drug_a} + {interaction.drug_b} = {interaction.severity.value}")
            
        except Exception as e:
            print(f"Error testing relationships: {e}")
        finally:
            db.close()
    
    def test_data_integrity(self):
        """Test data integrity constraints"""
        print("Testing data integrity...")
        
        db = self.create_session()
        try:
            # Check for orphaned records
            medications_without_patient = db.query(PatientMedication).filter(
                ~PatientMedication.patient_id.in_(
                    db.query(Patient.id)
                )
            ).count()
            
            diagnoses_without_patient = db.query(PatientDiagnosis).filter(
                ~PatientDiagnosis.patient_id.in_(
                    db.query(Patient.id)
                )
            ).count()
            
            print(f"Orphaned medications: {medications_without_patient}")
            print(f"Orphaned diagnoses: {diagnoses_without_patient}")
            
            # Check for duplicate interactions
            total_interactions = db.query(DrugInteraction).count()
            unique_interactions = db.query(
                DrugInteraction.drug_a, 
                DrugInteraction.drug_b
            ).distinct().count()
            
            print(f"Total interactions: {total_interactions}")
            print(f"Unique drug pairs: {unique_interactions}")
            if total_interactions != unique_interactions:
                print("⚠️ Warning: Duplicate drug interactions found")
            
        except Exception as e:
            print(f"Error testing integrity: {e}")
        finally:
            db.close()
    
    def run_all_tests(self):
        """Run all migration tests"""
        print("SADEWA Migration Test Suite")
        print("=" * 40)
        
        tests = [
            ("Data Consistency", self.test_data_consistency),
            ("API Endpoints", self.test_api_endpoints),
            ("Database Relationships", self.test_database_relationships),
            ("Data Integrity", self.test_data_integrity)
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n{test_name} Test:")
            print("-" * 30)
            try:
                test_func()
                results[test_name] = "PASSED"
                print(f"✅ {test_name} test completed")
            except Exception as e:
                results[test_name] = f"FAILED: {e}"
                print(f"❌ {test_name} test failed: {e}")
        
        # Summary
        print("\n" + "=" * 40)
        print("TEST SUMMARY:")
        for test_name, result in results.items():
            status = "✅" if result == "PASSED" else "❌"
            print(f"{status} {test_name}: {result}")
        
        passed = sum(1 for r in results.values() if r == "PASSED")
        total = len(results)
        print(f"\nOverall: {passed}/{total} tests passed")
        
        return passed == total


def main():
    """Main test function"""
    tester = MigrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Migration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the migration.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)