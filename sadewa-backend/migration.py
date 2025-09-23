# migration_to_no_rm.py
"""
Migration script untuk mengubah dari patient_id ke no_rm
✅ SAFE MIGRATION: Backup data sebelum migration
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NoRmMigration:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def backup_tables(self):
        """Backup existing tables before migration"""
        logger.info("🔄 Starting table backup...")
        
        with self.engine.connect() as conn:
            # Create backup tables
            backup_tables = [
                ("patient_medications", "patient_medications_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")),
                ("patient_allergies", "patient_allergies_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")),
                ("patient_timeline", "patient_timeline_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            ]
            
            for original, backup in backup_tables:
                try:
                    # Check if original table exists
                    result = conn.execute(text(f"SHOW TABLES LIKE '{original}'")).fetchone()
                    if result:
                        # Create backup
                        conn.execute(text(f"CREATE TABLE {backup} AS SELECT * FROM {original}"))
                        logger.info(f"✅ Backup created: {backup}")
                    else:
                        logger.info(f"⚠️ Table {original} does not exist, skipping backup")
                except Exception as e:
                    logger.error(f"❌ Error backing up {original}: {e}")
            
            conn.commit()
        
        logger.info("✅ Backup completed")
    
    def migrate_patient_medications(self):
        """Migrate patient_medications table to use no_rm"""
        logger.info("🔄 Migrating patient_medications table...")
        
        with self.engine.connect() as conn:
            try:
                # Check if table exists with old structure
                result = conn.execute(text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'patient_medications' 
                    AND COLUMN_NAME = 'patient_id'
                """)).fetchone()
                
                if result:
                    logger.info("📊 Found old structure, migrating data...")
                    
                    # Get existing data with no_rm mapping
                    existing_data = conn.execute(text("""
                        SELECT 
                            pm.*,
                            p.no_rm
                        FROM patient_medications pm
                        JOIN patients p ON pm.patient_id = p.id
                    """)).fetchall()
                    
                    if existing_data:
                        logger.info(f"📦 Found {len(existing_data)} records to migrate")
                        
                        # Drop and recreate table with new structure
                        conn.execute(text("DROP TABLE IF EXISTS patient_medications"))
                        
                        # Create new table structure
                        conn.execute(text("""
                            CREATE TABLE patient_medications (
                              id int NOT NULL AUTO_INCREMENT,
                              no_rm varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
                              medication_name varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
                              dosage varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                              frequency varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                              start_date date DEFAULT (CURDATE()),
                              end_date date DEFAULT NULL,
                              status enum('active','discontinued','completed') DEFAULT 'active',
                              prescribed_by varchar(255) DEFAULT NULL,
                              medical_record_id int DEFAULT NULL,
                              notes text DEFAULT NULL,
                              is_active tinyint(1) DEFAULT '1',
                              created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                              updated_at timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                              PRIMARY KEY (id),
                              KEY idx_medications_no_rm_active (no_rm,status,medication_name(100)),
                              KEY idx_medications_name (medication_name(100)),
                              KEY idx_medications_medical_record (medical_record_id),
                              CONSTRAINT fk_patient_medications_no_rm 
                                FOREIGN KEY (no_rm) REFERENCES patients (no_rm) 
                                ON DELETE CASCADE ON UPDATE CASCADE
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                        """))
                        
                        # Insert migrated data
                        for row in existing_data:
                            conn.execute(text("""
                                INSERT INTO patient_medications 
                                (no_rm, medication_name, dosage, frequency, 
                                 start_date, status, is_active, created_at)
                                VALUES 
                                (:no_rm, :medication_name, :dosage, :frequency,
                                 :created_at, 'active', :is_active, :created_at)
                            """), {
                                'no_rm': row.no_rm,
                                'medication_name': row.medication_name,
                                'dosage': row.dosage,
                                'frequency': row.frequency,
                                'is_active': row.is_active,
                                'created_at': row.created_at
                            })
                        
                        logger.info(f"✅ Migrated {len(existing_data)} medication records")
                    else:
                        logger.info("📋 No existing data to migrate")
                        
                        # Just create new table structure
                        conn.execute(text("DROP TABLE IF EXISTS patient_medications"))
                        conn.execute(text("""
                            CREATE TABLE patient_medications (
                              id int NOT NULL AUTO_INCREMENT,
                              no_rm varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
                              medication_name varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
                              dosage varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                              frequency varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                              start_date date DEFAULT (CURDATE()),
                              end_date date DEFAULT NULL,
                              status enum('active','discontinued','completed') DEFAULT 'active',
                              prescribed_by varchar(255) DEFAULT NULL,
                              medical_record_id int DEFAULT NULL,
                              notes text DEFAULT NULL,
                              is_active tinyint(1) DEFAULT '1',
                              created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                              updated_at timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                              PRIMARY KEY (id),
                              KEY idx_medications_no_rm_active (no_rm,status,medication_name(100)),
                              KEY idx_medications_name (medication_name(100)),
                              CONSTRAINT fk_patient_medications_no_rm 
                                FOREIGN KEY (no_rm) REFERENCES patients (no_rm) 
                                ON DELETE CASCADE ON UPDATE CASCADE
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                        """))
                else:
                    logger.info("✅ Table already has correct structure")
                
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Error migrating patient_medications: {e}")
                raise
    
    def migrate_patient_allergies(self):
        """Migrate patient_allergies table to use no_rm"""
        logger.info("🔄 Migrating patient_allergies table...")
        
        with self.engine.connect() as conn:
            try:
                # Check if no_rm column exists
                result = conn.execute(text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'patient_allergies' 
                    AND COLUMN_NAME = 'no_rm'
                """)).fetchone()
                
                if not result:
                    # Add no_rm column
                    conn.execute(text("ALTER TABLE patient_allergies ADD COLUMN no_rm varchar(50) AFTER id"))
                    
                    # Update no_rm values from patient_id
                    conn.execute(text("""
                        UPDATE patient_allergies pa 
                        SET pa.no_rm = (
                            SELECT p.no_rm 
                            FROM patients p 
                            WHERE p.id = pa.patient_id
                        ) 
                        WHERE pa.no_rm IS NULL
                    """))
                    
                    # Make no_rm NOT NULL
                    conn.execute(text("ALTER TABLE patient_allergies MODIFY COLUMN no_rm varchar(50) NOT NULL"))
                    
                    # Add foreign key constraint
                    conn.execute(text("""
                        ALTER TABLE patient_allergies 
                        ADD CONSTRAINT fk_patient_allergies_no_rm 
                        FOREIGN KEY (no_rm) REFERENCES patients (no_rm) 
                        ON DELETE CASCADE ON UPDATE CASCADE
                    """))
                    
                    # Add index
                    conn.execute(text("ALTER TABLE patient_allergies ADD KEY idx_allergies_no_rm (no_rm)"))
                    
                    logger.info("✅ Added no_rm column and constraints to patient_allergies")
                else:
                    logger.info("✅ patient_allergies already has no_rm column")
                
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Error migrating patient_allergies: {e}")
                raise
    
    def update_medical_records(self):
        """Add no_rm column to medical_records for better relations"""
        logger.info("🔄 Updating medical_records table...")
        
        with self.engine.connect() as conn:
            try:
                # Check if no_rm column exists
                result = conn.execute(text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'medical_records' 
                    AND COLUMN_NAME = 'no_rm'
                """)).fetchone()
                
                if not result:
                    # Add no_rm column
                    conn.execute(text("ALTER TABLE medical_records ADD COLUMN no_rm varchar(50) AFTER patient_id"))
                    
                    # Update no_rm values from patient_id
                    conn.execute(text("""
                        UPDATE medical_records mr 
                        SET mr.no_rm = (
                            SELECT p.no_rm 
                            FROM patients p 
                            WHERE p.id = mr.patient_id
                        ) 
                        WHERE mr.no_rm IS NULL
                    """))
                    
                    # Add index for performance
                    conn.execute(text("ALTER TABLE medical_records ADD KEY idx_medical_no_rm (no_rm)"))
                    
                    logger.info("✅ Added no_rm column to medical_records")
                else:
                    logger.info("✅ medical_records already has no_rm column")
                
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Error updating medical_records: {e}")
                raise
    
    def create_views_and_procedures(self):
        """Create helpful views and stored procedures"""
        logger.info("🔄 Creating views and stored procedures...")
        
        with self.engine.connect() as conn:
            try:
                # Create current medications view
                conn.execute(text("DROP VIEW IF EXISTS v_current_medications"))
                conn.execute(text("""
                    CREATE VIEW v_current_medications AS
                    SELECT 
                        pm.id,
                        pm.no_rm,
                        p.name as patient_name,
                        p.id as patient_id,
                        pm.medication_name,
                        pm.dosage,
                        pm.frequency,
                        pm.start_date,
                        pm.end_date,
                        pm.status,
                        pm.prescribed_by,
                        pm.created_at,
                        DATEDIFF(COALESCE(pm.end_date, CURDATE()), pm.start_date) as duration_days
                    FROM patient_medications pm
                    JOIN patients p ON pm.no_rm = p.no_rm
                    WHERE pm.status = 'active' 
                      AND pm.is_active = 1
                    ORDER BY pm.start_date DESC
                """))
                
                # Create medication summary view
                conn.execute(text("DROP VIEW IF EXISTS v_medication_summary"))
                conn.execute(text("""
                    CREATE VIEW v_medication_summary AS
                    SELECT 
                        p.no_rm,
                        p.name as patient_name,
                        COUNT(*) as total_medications,
                        COUNT(CASE WHEN pm.status = 'active' THEN 1 END) as active_medications,
                        COUNT(CASE WHEN pm.status = 'discontinued' THEN 1 END) as discontinued_medications,
                        MAX(pm.created_at) as last_medication_date
                    FROM patients p
                    LEFT JOIN patient_medications pm ON p.no_rm = pm.no_rm
                    GROUP BY p.no_rm, p.name
                """))
                
                logger.info("✅ Created views successfully")
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Error creating views: {e}")
                raise
    
    def verify_migration(self):
        """Verify migration was successful"""
        logger.info("🔍 Verifying migration...")
        
        with self.engine.connect() as conn:
            try:
                # Check patient_medications structure
                result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'patient_medications' 
                    AND COLUMN_NAME = 'no_rm'
                """)).fetchone()
                
                if result.count > 0:
                    logger.info("✅ patient_medications has no_rm column")
                else:
                    logger.error("❌ patient_medications missing no_rm column")
                
                # Check foreign key constraints
                fk_result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_NAME = 'patient_medications' 
                    AND CONSTRAINT_NAME = 'fk_patient_medications_no_rm'
                """)).fetchone()
                
                if fk_result.count > 0:
                    logger.info("✅ Foreign key constraints created")
                else:
                    logger.warning("⚠️ Foreign key constraints missing")
                
                # Count records
                count_result = conn.execute(text("SELECT COUNT(*) as count FROM patient_medications")).fetchone()
                logger.info(f"📊 Total medication records: {count_result.count}")
                
                # Check views
                view_result = conn.execute(text("SHOW TABLES LIKE 'v_current_medications'")).fetchone()
                if view_result:
                    logger.info("✅ Views created successfully")
                else:
                    logger.warning("⚠️ Views not found")
                
                logger.info("✅ Migration verification completed")
                
            except Exception as e:
                logger.error(f"❌ Error during verification: {e}")
    
    def run_full_migration(self):
        """Run complete migration process"""
        logger.info("🚀 Starting full migration to no_rm structure...")
        
        try:
            # Step 1: Backup existing data
            self.backup_tables()
            
            # Step 2: Migrate patient_medications
            self.migrate_patient_medications()
            
            # Step 3: Migrate patient_allergies
            self.migrate_patient_allergies()
            
            # Step 4: Update medical_records
            self.update_medical_records()
            
            # Step 5: Create views and procedures
            self.create_views_and_procedures()
            
            # Step 6: Verify migration
            self.verify_migration()
            
            logger.info("🎉 Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"💥 Migration failed: {e}")
            logger.info("🔄 You can restore from backup tables if needed")
            raise


def main():
    """Main migration function"""
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost/sadewa_db")
    
    print("="*60)
    print("🏥 SADEWA Database Migration to no_rm Structure")
    print("="*60)
    print("⚠️  IMPORTANT: This will modify your database structure!")
    print("📋 What this migration does:")
    print("   - Backup existing tables")
    print("   - Migrate patient_medications to use no_rm")
    print("   - Update patient_allergies with no_rm")
    print("   - Add no_rm to medical_records")
    print("   - Create helpful views")
    print("   - Verify migration success")
    print("="*60)
    
    # Confirmation
    confirm = input("Do you want to proceed? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Migration cancelled")
        return
    
    try:
        migration = NoRmMigration(DATABASE_URL)
        migration.run_full_migration()
        
        print("\n" + "="*60)
        print("🎉 MIGRATION SUCCESSFUL!")
        print("="*60)
        print("✅ Next steps:")
        print("   1. Update your application code to use new structure")
        print("   2. Test all medication-related functionality")
        print("   3. Remove backup tables after verification")
        print("   4. Update API endpoints to use no_rm")
        print("="*60)
        
    except Exception as e:
        print(f"\n💥 MIGRATION FAILED: {e}")
        print("🔄 Check backup tables for data recovery")
        print("📞 Contact support if you need help")


if __name__ == "__main__":
    main()


# ===== ROLLBACK SCRIPT =====

class MigrationRollback:
    """Rollback migration if needed"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
    
    def list_backup_tables(self):
        """List available backup tables"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE '%_backup_%'")).fetchall()
            return [row[0] for row in result]
    
    def restore_from_backup(self, backup_table: str, target_table: str):
        """Restore table from backup"""
        logger.info(f"🔄 Restoring {target_table} from {backup_table}")
        
        with self.engine.connect() as conn:
            try:
                # Drop current table
                conn.execute(text(f"DROP TABLE IF EXISTS {target_table}"))
                
                # Restore from backup
                conn.execute(text(f"CREATE TABLE {target_table} AS SELECT * FROM {backup_table}"))
                
                # Restore indexes (you may need to recreate these manually)
                if target_table == "patient_medications":
                    conn.execute(text(f"""
                        ALTER TABLE {target_table} 
                        ADD PRIMARY KEY (id),
                        ADD KEY idx_medications_patient_active (patient_id, is_active, medication_name(100))
                    """))
                
                conn.commit()
                logger.info(f"✅ Restored {target_table}")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Error restoring {target_table}: {e}")
                raise
    
    def rollback_migration(self):
        """Rollback complete migration"""
        logger.info("🔄 Starting migration rollback...")
        
        backup_tables = self.list_backup_tables()
        if not backup_tables:
            logger.error("❌ No backup tables found!")
            return
        
        logger.info(f"📋 Found backup tables: {backup_tables}")
        
        # Find most recent backups
        medication_backups = [t for t in backup_tables if 'patient_medications_backup' in t]
        allergy_backups = [t for t in backup_tables if 'patient_allergies_backup' in t]
        
        if medication_backups:
            latest_med_backup = sorted(medication_backups)[-1]
            self.restore_from_backup(latest_med_backup, "patient_medications")
        
        if allergy_backups:
            latest_allergy_backup = sorted(allergy_backups)[-1]
            self.restore_from_backup(latest_allergy_backup, "patient_allergies")
        
        logger.info("✅ Rollback completed")


# ===== USAGE EXAMPLES =====

def example_usage():
    """Example of how to use the migration"""
    
    # Run migration
    # python migration_to_no_rm.py
    
    # Or programmatically:
    """
    from migration_to_no_rm import NoRmMigration
    
    migration = NoRmMigration("mysql+pymysql://user:pass@localhost/db")
    migration.run_full_migration()
    """
    
    # Rollback if needed:
    """
    from migration_to_no_rm import MigrationRollback
    
    rollback = MigrationRollback("mysql+pymysql://user:pass@localhost/db")
    rollback.rollback_migration()
    """


# ===== TEST FUNCTIONS =====

def test_migration(database_url: str):
    """Test migration with sample data"""
    logger.info("🧪 Testing migration with sample data...")
    
    migration = NoRmMigration(database_url)
    
    with migration.engine.connect() as conn:
        try:
            # Insert test patient
            conn.execute(text("""
                INSERT IGNORE INTO patients (id, no_rm, name, age, gender) 
                VALUES (999, 'TEST001', 'Test Patient', 30, 'male')
            """))
            
            # Insert test medication (old structure)
            conn.execute(text("""
                INSERT IGNORE INTO patient_medications (patient_id, medication_name, dosage, frequency) 
                VALUES (999, 'Test Medicine', '500mg', '2x sehari')
            """))
            
            conn.commit()
            
            # Run migration
            migration.run_full_migration()
            
            # Verify test data
            result = conn.execute(text("""
                SELECT * FROM patient_medications WHERE no_rm = 'TEST001'
            """)).fetchone()
            
            if result:
                logger.info("✅ Test migration successful")
                
                # Cleanup test data
                conn.execute(text("DELETE FROM patient_medications WHERE no_rm = 'TEST001'"))
                conn.execute(text("DELETE FROM patients WHERE no_rm = 'TEST001'"))
                conn.commit()
            else:
                logger.error("❌ Test migration failed")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Test failed: {e}")


# ===== MONITORING FUNCTIONS =====

def monitor_migration_progress():
    """Monitor migration progress"""
    logger.info("📊 Migration Progress Monitor")
    logger.info("This would show real-time progress in a production environment")
    
    # In production, you might want to:
    # - Show percentage complete
    # - Estimate time remaining
    # - Show current operation
    # - Alert on errors
    
    pass


def generate_migration_report(database_url: str):
    """Generate post-migration report"""
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Count records in each table
        tables_info = []
        
        tables = ['patients', 'patient_medications', 'patient_allergies', 'medical_records']
        
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}")).fetchone()
                tables_info.append({'table': table, 'count': result.count})
            except Exception as e:
                tables_info.append({'table': table, 'count': f'Error: {e}'})
        
        # Generate report
        report = {
            'migration_date': datetime.now().isoformat(),
            'tables': tables_info,
            'views_created': ['v_current_medications', 'v_medication_summary'],
            'status': 'completed'
        }
        
        # Save report
        with open(f'migration_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("📋 Migration report generated")
        return report


# ===== MAIN EXECUTION =====

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # Run test migration
            db_url = sys.argv[2] if len(sys.argv) > 2 else os.getenv("DATABASE_URL")
            test_migration(db_url)
            
        elif command == "rollback":
            # Run rollback
            db_url = sys.argv[2] if len(sys.argv) > 2 else os.getenv("DATABASE_URL")
            rollback = MigrationRollback(db_url)
            rollback.rollback_migration()
            
        elif command == "report":
            # Generate report
            db_url = sys.argv[2] if len(sys.argv) > 2 else os.getenv("DATABASE_URL")
            generate_migration_report(db_url)
            
        else:
            print("❌ Unknown command. Use: test, rollback, or report")
    else:
        # Run main migration
        main()