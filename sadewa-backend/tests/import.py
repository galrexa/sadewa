#!/usr/bin/env python3
"""
Migration Script: JSON to Database
SADEWA - Smart Assistant for Drug & Evidence Warning

Migrates patient data and drug interactions from JSON files to MySQL database.
Run this script after setting up the database schema.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.database import get_database_url, engine
from app.models import (
    Base, Patient, PatientMedication, PatientDiagnosis, 
    PatientAllergy, DrugInteraction, ICD10, GenderEnum, SeverityEnum
)

class MigrationManager:
    def __init__(self):
        self.engine = engine
        if not self.engine:
            print("❌ Database engine not available")
            sys.exit(1)
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.data_dir = Path(__file__).parent.parent / "sadewa-backend/data"
        
    def create_session(self):
        """Create a new database session"""
        return self.SessionLocal()
    
    def load_json_file(self, filename: str):
        """Load data from JSON file"""
        file_path = self.data_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Loaded {len(data)} records from {filename}")
                return data
        except FileNotFoundError:
            print(f"⚠️ File not found: {filename}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in {filename}: {e}")
            return []
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to create tables: {e}")
            return False
    
    def clear_existing_data(self, db):
        """Clear existing data for clean migration"""
        try:
            # Delete in reverse order due to foreign key constraints
            db.query(PatientMedication).delete()
            db.query(PatientDiagnosis).delete()
            db.query(PatientAllergy).delete()
            db.query(DrugInteraction).delete()
            db.query(Patient).delete()
            # Don't delete ICD10 as it's reference data
            
            db.commit()
            print("✅ Existing data cleared")
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to clear existing data: {e}")
            raise
    
    def migrate_patients(self, db):
        """Migrate patient data from JSON to database"""
        patients_data = self.load_json_file("patients.json")
        if not patients_data:
            print("⚠️ No patient data to migrate")
            return
        
        migrated_count = 0
        for patient_json in patients_data:
            try:
                # Extract patient ID number from string like "P001"
                patient_id_str = patient_json.get('id', '')
                if patient_id_str.startswith('P'):
                    patient_id = int(patient_id_str[1:])  # Remove 'P' and convert to int
                else:
                    patient_id = migrated_count + 1  # Fallback ID
                
                # Create patient record
                patient = Patient(
                    id=patient_id,
                    name=patient_json.get('name', 'Unknown'),
                    age=patient_json.get('age', 0),
                    gender=GenderEnum.male if patient_json.get('gender', '').lower() == 'male' else GenderEnum.female,
                    weight_kg=patient_json.get('weight_kg', 70),
                    phone=patient_json.get('phone', None)
                )
                
                db.add(patient)
                db.flush()  # Get the patient ID for relationships
                
                # Migrate medications
                medications = patient_json.get('current_medications', [])
                for med_text in medications:
                    # Parse medication string (e.g., "Warfarin 5mg OD (for AF stroke prevention)")
                    parts = med_text.split()
                    medication_name = parts[0] if parts else med_text
                    dosage = ' '.join(parts[1:]) if len(parts) > 1 else ''
                    
                    medication = PatientMedication(
                        patient_id=patient.id,
                        medication_name=medication_name,
                        dosage=dosage,
                        is_active=True
                    )
                    db.add(medication)
                
                # Migrate diagnoses
                diagnoses = patient_json.get('diagnoses_text', [])
                for diag_text in diagnoses:
                    diagnosis = PatientDiagnosis(
                        patient_id=patient.id,
                        diagnosis_text=diag_text
                        # icd_code will be populated later if ICD-10 data is available
                    )
                    db.add(diagnosis)
                
                # Migrate allergies
                allergies = patient_json.get('allergies', [])
                for allergy_text in allergies:
                    # Parse allergy string (e.g., "Penicillin (rash)")
                    if '(' in allergy_text:
                        allergen = allergy_text.split('(')[0].strip()
                        reaction = allergy_text.split('(')[1].rstrip(')').strip()
                    else:
                        allergen = allergy_text
                        reaction = None
                    
                    allergy = PatientAllergy(
                        patient_id=patient.id,
                        allergen=allergen,
                        reaction_type=reaction
                    )
                    db.add(allergy)
                
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Error migrating patient {patient_json.get('name', 'Unknown')}: {e}")
                continue
        
        try:
            db.commit()
            print(f"✅ Migrated {migrated_count} patients with related data")
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to commit patient migration: {e}")
            raise
    
    def migrate_drug_interactions(self, db):
        """Migrate drug interaction data from JSON to database"""
        interactions_data = self.load_json_file("drug_interactions.json")
        if not interactions_data:
            print("⚠️ No drug interaction data to migrate")
            return
        
        migrated_count = 0
        for interaction_json in interactions_data:
            try:
                # Map severity from string to enum
                severity_str = interaction_json.get('severity', 'MODERATE').upper()
                if severity_str in [s.value for s in SeverityEnum]:
                    severity = SeverityEnum(severity_str)
                else:
                    severity = SeverityEnum.MODERATE  # Default
                
                interaction = DrugInteraction(
                    drug_a=interaction_json.get('drug_a', ''),
                    drug_b=interaction_json.get('drug_b', ''),
                    severity=severity,
                    mechanism=interaction_json.get('mechanism', ''),
                    clinical_effect=interaction_json.get('clinical_effect', ''),
                    recommendation=interaction_json.get('recommendation', ''),
                    monitoring=interaction_json.get('monitoring', ''),
                    evidence_level=interaction_json.get('evidence_level', 'Unknown'),
                    is_active=True
                )
                
                db.add(interaction)
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Error migrating interaction {interaction_json.get('drug_a', '')}-{interaction_json.get('drug_b', '')}: {e}")
                continue
        
        try:
            db.commit()
            print(f"✅ Migrated {migrated_count} drug interactions")
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to commit drug interaction migration: {e}")
            raise
    
    def verify_migration(self, db):
        """Verify that migration was successful"""
        try:
            patient_count = db.query(Patient).count()
            medication_count = db.query(PatientMedication).count()
            diagnosis_count = db.query(PatientDiagnosis).count()
            allergy_count = db.query(PatientAllergy).count()
            interaction_count = db.query(DrugInteraction).count()
            
            print("\n📊 Migration Verification:")
            print(f"   Patients: {patient_count}")
            print(f"   Medications: {medication_count}")
            print(f"   Diagnoses: {diagnosis_count}")
            print(f"   Allergies: {allergy_count}")
            print(f"   Drug Interactions: {interaction_count}")
            
            # Test a sample query
            if patient_count > 0:
                sample_patient = db.query(Patient).first()
                med_count = len(sample_patient.medications)
                diag_count = len(sample_patient.diagnoses)
                print(f"   Sample patient '{sample_patient.name}' has {med_count} medications, {diag_count} diagnoses")
            
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def add_sample_icd10_data(self, db):
        """Add some sample ICD-10 codes for testing"""
        sample_icds = [
            {"code": "E11", "name_en": "Type 2 diabetes mellitus", "name_id": "Diabetes mellitus tipe 2", "category": "E00-E89"},
            {"code": "I10", "name_en": "Essential hypertension", "name_id": "Hipertensi esensial", "category": "I00-I99"},
            {"code": "I48", "name_en": "Atrial fibrillation", "name_id": "Fibrilasi atrial", "category": "I00-I99"},
            {"code": "I25", "name_en": "Chronic ischaemic heart disease", "name_id": "Penyakit jantung iskemik kronik", "category": "I00-I99"},
            {"code": "I50", "name_en": "Heart failure", "name_id": "Gagal jantung", "category": "I00-I99"},
            {"code": "N18", "name_en": "Chronic kidney disease", "name_id": "Penyakit ginjal kronik", "category": "N00-N99"},
            {"code": "J44", "name_en": "Chronic obstructive pulmonary disease", "name_id": "Penyakit paru obstruktif kronik", "category": "J00-J99"},
            {"code": "E78", "name_en": "Disorders of lipoprotein metabolism", "name_id": "Gangguan metabolisme lipoprotein", "category": "E00-E89"},
        ]
        
        migrated_count = 0
        for icd_data in sample_icds:
            try:
                # Check if already exists
                existing = db.query(ICD10).filter(ICD10.code == icd_data['code']).first()
                if not existing:
                    icd = ICD10(
                        code=icd_data['code'],
                        name_en=icd_data['name_en'],
                        name_id=icd_data['name_id'],
                        category=icd_data['category']
                    )
                    db.add(icd)
                    migrated_count += 1
            except Exception as e:
                print(f"❌ Error adding ICD-10 {icd_data['code']}: {e}")
                continue
        
        try:
            db.commit()
            print(f"✅ Added {migrated_count} sample ICD-10 codes")
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to commit ICD-10 data: {e}")
    
    def run_migration(self, clear_existing=True):
        """Run the complete migration process"""
        print("🚀 Starting SADEWA JSON to Database Migration")
        print(f"   Database URL: {get_database_url()}")
        print(f"   Data directory: {self.data_dir}")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print("-" * 60)
        
        # Create tables
        if not self.create_tables():
            return False
        
        # Create database session
        db = self.create_session()
        try:
            # Clear existing data if requested
            if clear_existing:
                print("🗑️ Clearing existing data...")
                self.clear_existing_data(db)
            
            # Add sample ICD-10 data first
            print("📝 Adding sample ICD-10 data...")
            self.add_sample_icd10_data(db)
            
            # Migrate patients and related data
            print("👥 Migrating patients...")
            self.migrate_patients(db)
            
            # Migrate drug interactions
            print("💊 Migrating drug interactions...")
            self.migrate_drug_interactions(db)
            
            # Verify migration
            print("✅ Verifying migration...")
            if self.verify_migration(db):
                print("\n🎉 Migration completed successfully!")
                return True
            else:
                print("\n❌ Migration verification failed!")
                return False
                
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.rollback()
            return False
        finally:
            db.close()


def main():
    """Main migration function"""
    print("SADEWA - JSON to Database Migration Tool")
    print("="*50)
    
    # Check if data files exist
    migration_manager = MigrationManager()
    
    patients_file = migration_manager.data_dir / "patients.json"
    interactions_file = migration_manager.data_dir / "drug_interactions.json"
    
    if not patients_file.exists():
        print(f"❌ Patients file not found: {patients_file}")
        return False
    
    if not interactions_file.exists():
        print(f"❌ Drug interactions file not found: {interactions_file}")
        return False
    
    # Ask for confirmation
    response = input("\n⚠️ This will replace existing data in the database. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return False
    
    # Run migration
    success = migration_manager.run_migration(clear_existing=True)
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now use the database-powered API endpoints.")
    else:
        print("\n❌ Migration failed. Check the error messages above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)