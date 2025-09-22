# populate_drug_interactions.py
"""
Populate drug interactions database dengan data sample
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

# Sample drug interactions data
DRUG_INTERACTIONS = [
    {
        "drug_1": "Warfarin",
        "drug_2": "Aspirin", 
        "severity": "MAJOR",
        "description": "Increased risk of bleeding due to combined anticoagulant and antiplatelet effects",
        "mechanism": "Additive anticoagulant effect",
        "clinical_effect": "Serious bleeding complications possible",
        "recommendation": "Monitor PT/INR closely, consider alternative antiplatelet agent",
        "monitoring": "Weekly PT/INR monitoring initially",
        "evidence_level": "High"
    },
    {
        "drug_1": "Warfarin",
        "drug_2": "Ibuprofen",
        "severity": "MAJOR", 
        "description": "NSAIDs increase bleeding risk in patients on warfarin",
        "mechanism": "Platelet inhibition + anticoagulation",
        "clinical_effect": "GI bleeding, prolonged bleeding time",
        "recommendation": "Avoid combination if possible, use paracetamol instead",
        "monitoring": "Monitor for signs of bleeding",
        "evidence_level": "High"
    },
    {
        "drug_1": "Aspirin",
        "drug_2": "Ibuprofen",
        "severity": "MODERATE",
        "description": "Increased risk of GI bleeding and ulceration",
        "mechanism": "Combined COX inhibition",
        "clinical_effect": "GI irritation and bleeding",
        "recommendation": "Monitor for GI symptoms, consider gastroprotection",
        "monitoring": "Monitor for abdominal pain, black stools",
        "evidence_level": "Moderate"
    },
    {
        "drug_1": "Simvastatin",
        "drug_2": "Warfarin",
        "severity": "MODERATE",
        "description": "Statins may enhance anticoagulant effect of warfarin",
        "mechanism": "CYP450 interaction, protein binding displacement",
        "clinical_effect": "Increased INR, bleeding risk",
        "recommendation": "Monitor INR when starting/stopping statin",
        "monitoring": "INR monitoring for 4-6 weeks",
        "evidence_level": "Moderate"
    },
    {
        "drug_1": "Metformin",
        "drug_2": "Contrast Media",
        "severity": "MAJOR",
        "description": "Risk of lactic acidosis with contrast procedures",
        "mechanism": "Impaired renal function",
        "clinical_effect": "Lactic acidosis",
        "recommendation": "Stop metformin 48h before contrast, restart after normal renal function",
        "monitoring": "Monitor renal function",
        "evidence_level": "High"
    },
    {
        "drug_1": "ACE Inhibitor",
        "drug_2": "Potassium Supplements",
        "severity": "MODERATE",
        "description": "Risk of hyperkalemia",
        "mechanism": "Reduced potassium excretion",
        "clinical_effect": "Hyperkalemia, cardiac arrhythmias",
        "recommendation": "Monitor serum potassium regularly",
        "monitoring": "Serum K+ every 1-2 weeks initially",
        "evidence_level": "Moderate"
    },
    {
        "drug_1": "Digoxin",
        "drug_2": "Amiodarone",
        "severity": "MAJOR",
        "description": "Amiodarone increases digoxin levels",
        "mechanism": "P-glycoprotein inhibition",
        "clinical_effect": "Digoxin toxicity",
        "recommendation": "Reduce digoxin dose by 50%, monitor levels",
        "monitoring": "Digoxin levels, ECG monitoring",
        "evidence_level": "High"
    },
    {
        "drug_1": "Theophylline",
        "drug_2": "Ciprofloxacin",
        "severity": "MAJOR",
        "description": "Ciprofloxacin inhibits theophylline metabolism",
        "mechanism": "CYP1A2 inhibition",
        "clinical_effect": "Theophylline toxicity",
        "recommendation": "Monitor theophylline levels, reduce dose",
        "monitoring": "Theophylline levels, clinical signs of toxicity",
        "evidence_level": "High"
    },
    {
        "drug_1": "Lithium",
        "drug_2": "ACE Inhibitor",
        "severity": "MAJOR",
        "description": "ACE inhibitors increase lithium levels",
        "mechanism": "Reduced renal lithium clearance",
        "clinical_effect": "Lithium toxicity",
        "recommendation": "Monitor lithium levels closely",
        "monitoring": "Lithium levels weekly initially",
        "evidence_level": "High"
    },
    {
        "drug_1": "Paracetamol",
        "drug_2": "Warfarin",
        "severity": "MINOR",
        "description": "High dose paracetamol may enhance warfarin effect",
        "mechanism": "Unknown mechanism",
        "clinical_effect": "Slight increase in INR",
        "recommendation": "Monitor INR with regular paracetamol use",
        "monitoring": "INR monitoring if chronic use",
        "evidence_level": "Low"
    }
]

# Simple drug interactions for quick lookup
SIMPLE_INTERACTIONS = [
    {
        "drug_a": "Warfarin",
        "drug_b": "Aspirin",
        "severity": "Major",
        "description": "Meningkatkan risiko perdarahan secara signifikan",
        "recommendation": "Hindari kombinasi, pertimbangkan alternatif"
    },
    {
        "drug_a": "Warfarin", 
        "drug_b": "Ibuprofen",
        "severity": "Major",
        "description": "Risiko perdarahan saluran cerna meningkat",
        "recommendation": "Gunakan paracetamol sebagai alternatif"
    },
    {
        "drug_a": "Aspirin",
        "drug_b": "Ibuprofen", 
        "severity": "Moderate",
        "description": "Meningkatkan risiko iritasi dan perdarahan lambung",
        "recommendation": "Monitor gejala gastrointestinal"
    },
    {
        "drug_a": "Metformin",
        "drug_b": "Kontras Media",
        "severity": "Major", 
        "description": "Risiko asidosis laktat pada prosedur kontras",
        "recommendation": "Hentikan metformin 48 jam sebelum prosedur"
    },
    {
        "drug_a": "Simvastatin",
        "drug_b": "Warfarin",
        "severity": "Moderate",
        "description": "Dapat meningkatkan efek antikoagulan",
        "recommendation": "Monitor INR saat memulai/menghentikan statin"
    }
]

def get_database_config():
    """Get database configuration"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Parse DATABASE_URL
        if database_url.startswith('DATABASE_URL='):
            database_url = database_url.replace('DATABASE_URL=', '')
        
        if database_url.startswith('mysql+pymysql://'):
            database_url = database_url.replace('mysql+pymysql://', 'mysql://')
        
        # Parse URL: mysql://user:password@host:port/database
        try:
            database_url = database_url.replace('mysql://', '')
            
            if '@' in database_url:
                auth_part, host_part = database_url.split('@', 1)
                
                if ':' in auth_part:
                    user, password = auth_part.split(':', 1)
                else:
                    user = auth_part
                    password = ''
                
                if '/' in host_part:
                    host_port, database = host_part.split('/', 1)
                else:
                    host_port = host_part
                    database = 'sadewa_db'
                
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                    port = int(port)
                else:
                    host = host_port
                    port = 3306
                
                return {
                    'host': host,
                    'port': port,
                    'user': user,
                    'password': password,
                    'database': database
                }
        except Exception as e:
            print(f"Error parsing DATABASE_URL: {e}")
    
    # Fallback configuration
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'sadewa_db')
    }

def populate_drug_interactions():
    """Populate drug interactions tables"""
    print("💊 Populating Drug Interactions Database")
    print("=" * 45)
    
    config = get_database_config()
    
    try:
        # Connect to database
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print(f"✅ Connected to database: {config['database']}")
        
        # 1. Clear existing data
        print("\n🗑️  Clearing existing interaction data...")
        cursor.execute("DELETE FROM drug_interactions")
        cursor.execute("DELETE FROM simple_drug_interactions") 
        print("✅ Existing data cleared")
        
        # 2. Insert detailed drug interactions
        print(f"\n📊 Inserting {len(DRUG_INTERACTIONS)} detailed interactions...")
        
        detailed_insert = """
        INSERT INTO drug_interactions (
            drug_1, drug_2, severity, description, mechanism, 
            clinical_effect, recommendation, monitoring, evidence_level, 
            is_active, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW()
        )
        """
        
        for interaction in DRUG_INTERACTIONS:
            cursor.execute(detailed_insert, (
                interaction['drug_1'],
                interaction['drug_2'], 
                interaction['severity'],
                interaction['description'],
                interaction['mechanism'],
                interaction['clinical_effect'],
                interaction['recommendation'],
                interaction['monitoring'],
                interaction['evidence_level']
            ))
        
        print(f"✅ {len(DRUG_INTERACTIONS)} detailed interactions inserted")
        
        # 3. Insert simple drug interactions
        print(f"\n📋 Inserting {len(SIMPLE_INTERACTIONS)} simple interactions...")
        
        simple_insert = """
        INSERT INTO simple_drug_interactions (
            drug_a, drug_b, severity, description, recommendation, 
            is_active, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, 1, NOW()
        )
        """
        
        for interaction in SIMPLE_INTERACTIONS:
            cursor.execute(simple_insert, (
                interaction['drug_a'],
                interaction['drug_b'],
                interaction['severity'],
                interaction['description'],
                interaction['recommendation']
            ))
        
        print(f"✅ {len(SIMPLE_INTERACTIONS)} simple interactions inserted")
        
        # 4. Add reverse interactions (drug_b -> drug_a)
        print(f"\n🔄 Adding reverse interactions...")
        
        reverse_count = 0
        for interaction in SIMPLE_INTERACTIONS:
            cursor.execute(simple_insert, (
                interaction['drug_b'],  # Swap drug positions
                interaction['drug_a'],
                interaction['severity'],
                interaction['description'],
                interaction['recommendation']
            ))
            reverse_count += 1
        
        print(f"✅ {reverse_count} reverse interactions added")
        
        # 5. Commit changes
        connection.commit()
        
        # 6. Verify data
        print(f"\n🔍 Verifying inserted data...")
        
        cursor.execute("SELECT COUNT(*) FROM drug_interactions")
        detailed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM simple_drug_interactions")
        simple_count = cursor.fetchone()[0]
        
        print(f"✅ Verification complete:")
        print(f"   📊 Detailed interactions: {detailed_count}")
        print(f"   📋 Simple interactions: {simple_count}")
        
        # 7. Test sample queries
        print(f"\n🧪 Testing sample queries...")
        
        # Test Warfarin + Aspirin
        test_query = """
        SELECT drug_a, drug_b, severity, description 
        FROM simple_drug_interactions 
        WHERE (LOWER(drug_a) LIKE %s AND LOWER(drug_b) LIKE %s)
           OR (LOWER(drug_a) LIKE %s AND LOWER(drug_b) LIKE %s)
        LIMIT 1
        """
        
        cursor.execute(test_query, ('%warfarin%', '%aspirin%', '%aspirin%', '%warfarin%'))
        test_result = cursor.fetchone()
        
        if test_result:
            print(f"✅ Test query successful:")
            print(f"   {test_result[0]} + {test_result[1]} = {test_result[2]} ({test_result[3][:50]}...)")
        else:
            print(f"⚠️  Test query returned no results")
        
        cursor.close()
        connection.close()
        
        print(f"\n🎉 Drug interactions database populated successfully!")
        print("=" * 45)
        return True
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_test_drugs():
    """Create test drugs in drugs table if needed"""
    print("\n💊 Ensuring test drugs exist in drugs table...")
    
    config = get_database_config()
    test_drugs = [
        ("Warfarin", "Warfarin"),
        ("Aspirin", "Aspirin"), 
        ("Ibuprofen", "Ibuprofen"),
        ("Paracetamol", "Acetaminophen"),
        ("Simvastatin", "Simvastatin"),
        ("Metformin", "Metformin"),
        ("Omeprazole", "Omeprazole"),
        ("Vitamin C", "Ascorbic Acid"),
        ("Amoxicillin", "Amoxicillin"),
        ("Ciprofloxacin", "Ciprofloxacin")
    ]
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Check if drugs table exists and has data
        cursor.execute("SELECT COUNT(*) FROM drugs")
        existing_count = cursor.fetchone()[0]
        
        if existing_count < 5:  # If few drugs exist, add test drugs
            print(f"📊 Adding test drugs to database...")
            
            insert_drug = """
            INSERT IGNORE INTO drugs (nama_obat, nama_obat_internasional, is_active, created_at, updated_at)
            VALUES (%s, %s, 1, NOW(), NOW())
            """
            
            for drug_id, drug_intl in test_drugs:
                cursor.execute(insert_drug, (drug_id, drug_intl))
            
            connection.commit()
            print(f"✅ Test drugs added")
        else:
            print(f"✅ Drugs table already has {existing_count} entries")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error creating test drugs: {e}")
        return False

def test_interaction_api():
    """Test the interaction API with sample data"""
    print(f"\n🧪 Testing Interaction API...")
    
    try:
        import requests
        
        # Test data
        test_data = {
            "medications": ["Warfarin", "Aspirin"],
            "include_cache": False
        }
        
        response = requests.post(
            "http://localhost:8000/api/analyze/drug-interactions",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            interactions = result.get('total_interactions', 0)
            print(f"✅ API test successful: {interactions} interactions found")
            
            if interactions > 0:
                print("✅ Drug interaction detection is working!")
            else:
                print("⚠️  No interactions detected - check drug names matching")
        else:
            print(f"❌ API test failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
    except ImportError:
        print("⚠️  requests library not available for API testing")
    except Exception as e:
        print(f"❌ API test error: {e}")

def main():
    """Main function"""
    print("💊 SADEWA Drug Interactions Database Setup")
    print("=" * 50)
    
    # Step 1: Create test drugs
    if not create_test_drugs():
        print("❌ Failed to create test drugs")
        return
    
    # Step 2: Populate interactions
    if not populate_drug_interactions():
        print("❌ Failed to populate drug interactions")
        return
    
    # Step 3: Test API (optional)
    test_interaction_api()
    
    print(f"\n🎯 Setup Complete!")
    print("=" * 50)
    print("📚 What was done:")
    print("• Test drugs added to drugs table")
    print("• Detailed drug interactions populated")
    print("• Simple drug interactions populated")
    print("• Reverse interactions added for better matching")
    print("• Database queries tested")
    print()
    print("📝 Next steps:")
    print("• Test drug interaction API endpoints")
    print("• Verify interaction detection is working")
    print("• Add more drug combinations as needed")

if __name__ == "__main__":
    main()