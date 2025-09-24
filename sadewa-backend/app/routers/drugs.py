# app/routers/drugs.py - Fixed with SQLAlchemy connection
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.database import engine
from sqlalchemy import text
import time

router = APIRouter()

@router.get("/stats")
async def get_drug_stats():
    """Get drug database statistics"""
    try:
        with engine.connect() as connection:
            # Get total drugs
            total_result = connection.execute(text("SELECT COUNT(*) as total FROM drugs"))
            total_drugs = total_result.scalar()
            
            # Get active drugs
            active_result = connection.execute(text("SELECT COUNT(*) as active FROM drugs WHERE is_active = 1"))
            active_drugs = active_result.scalar()
            
            # Get sample drugs
            sample_result = connection.execute(text("""
                SELECT nama_obat, nama_obat_internasional 
                FROM drugs 
                WHERE is_active = 1 
                ORDER BY created_at DESC 
                LIMIT 10
            """))
            sample_drugs = [{"nama_obat": row[0], "nama_obat_internasional": row[1]} for row in sample_result.fetchall()]
        
        return {
            "total_drugs": total_drugs,
            "active_drugs": active_drugs,
            "inactive_drugs": total_drugs - active_drugs,
            "sample_drugs": sample_drugs,
            "database_status": "connected",
            "last_updated": "2024-01-15"
        }
        
    except Exception as e:
        print(f"Database error in get_drug_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/search")
async def search_drugs(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """Search drugs in database"""
    try:
        start_time = time.time()
        
        with engine.connect() as connection:
            # Simple search query (avoiding complex MATCH syntax for compatibility)
            search_query = text("""
                SELECT 
                    id,
                    nama_obat,
                    nama_obat_internasional,
                    is_active,
                    CASE 
                        WHEN LOWER(nama_obat) LIKE LOWER(:exact_match) THEN 4
                        WHEN LOWER(nama_obat_internasional) LIKE LOWER(:exact_match) THEN 3
                        WHEN LOWER(nama_obat) LIKE LOWER(:search_term) THEN 2
                        ELSE 1
                    END as relevance_score
                FROM drugs 
                WHERE (
                    LOWER(nama_obat) LIKE LOWER(:search_term) OR 
                    LOWER(nama_obat_internasional) LIKE LOWER(:search_term)
                )
                AND is_active = 1
                ORDER BY relevance_score DESC, nama_obat ASC
                LIMIT :limit_val
            """)
            
            search_params = {
                "search_term": f"%{q}%",
                "exact_match": f"{q}%",
                "limit_val": limit
            }
            
            result = connection.execute(search_query, search_params)
            drugs = []
            for row in result.fetchall():
                drugs.append({
                    "id": row[0],
                    "nama_obat": row[1],
                    "nama_obat_internasional": row[2],
                    "is_active": row[3],
                })
            
            # Get total count
            count_query = text("""
                SELECT COUNT(*) 
                FROM drugs 
                WHERE (
                    LOWER(nama_obat) LIKE LOWER(:search_term) OR 
                    LOWER(nama_obat_internasional) LIKE LOWER(:search_term)
                )
                AND is_active = 1
            """)
            count_result = connection.execute(count_query, {"search_term": f"%{q}%"})
            total_count = count_result.scalar()
        
        query_time = time.time() - start_time
        
        return {
            "query": q,
            "total_found": total_count,
            "returned": len(drugs),
            "query_time": round(query_time, 3),
            "drugs": drugs
        }
        
    except Exception as e:
        print(f"Database error in search_drugs: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/by-name")
async def get_drug_by_name(name: str = Query(..., description="Exact drug name")):
    """Get drug by exact name match"""
    try:
        with engine.connect() as connection:
            search_query = text("""
                SELECT id, nama_obat, nama_obat_internasional, is_active, created_at
                FROM drugs 
                WHERE (LOWER(nama_obat) = LOWER(:name) OR LOWER(nama_obat_internasional) = LOWER(:name))
                AND is_active = 1
                LIMIT 1
            """)
            
            result = connection.execute(search_query, {"name": name})
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail=f"Drug '{name}' not found")
            
            drug = {
                "id": row[0],
                "nama_obat": row[1],
                "nama_obat_internasional": row[2],
                "is_active": row[3]
            }
        
        return {"drug": drug}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_drug_by_name: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/popular")
async def get_popular_drugs(limit: int = Query(10, ge=1, le=20)):
    """Get popular/common drugs"""
    try:
        with engine.connect() as connection:
            # Get common drugs based on name patterns
            popular_query = text("""
                SELECT id, nama_obat, nama_obat_internasional, is_active
                FROM drugs 
                WHERE is_active = 1 
                AND (
                    LOWER(nama_obat) LIKE 'para%' OR 
                    LOWER(nama_obat) LIKE 'ibu%' OR
                    LOWER(nama_obat) LIKE 'amo%' OR
                    LOWER(nama_obat) LIKE 'ome%' OR
                    LOWER(nama_obat) LIKE 'met%' OR
                    LOWER(nama_obat) LIKE 'aml%' OR
                    LOWER(nama_obat) LIKE 'sim%' OR
                    LOWER(nama_obat) LIKE 'los%' OR
                    LOWER(nama_obat) LIKE 'asp%'
                )
                ORDER BY nama_obat ASC
                LIMIT :limit_val
            """)
            
            result = connection.execute(popular_query, {"limit_val": limit})
            drugs = []
            for row in result.fetchall():
                drugs.append({
                    "id": row[0],
                    "nama_obat": row[1],
                    "nama_obat_internasional": row[2],
                    "is_active": row[3]
                })
        
        return {
            "popular_drugs": drugs,
            "count": len(drugs)
        }
        
    except Exception as e:
        print(f"Database error in get_popular_drugs: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/check-interactions")
async def check_drug_interactions(drug_names: str = Query(..., description="Comma-separated drug names")):
    """Check interactions between multiple drugs"""
    try:
        # Parse drug names
        drugs = [name.strip() for name in drug_names.split(",") if name.strip()]
        
        if len(drugs) < 2:
            return {
                "input_drugs": drugs,
                "interactions_found": 0,
                "interactions": [],
                "message": "At least 2 drugs required for interaction check"
            }
        
        with engine.connect() as connection:
            # Validate drugs exist in database
            validated_drugs = []
            for drug_name in drugs:
                search_query = text("""
                    SELECT nama_obat, nama_obat_internasional
                    FROM drugs 
                    WHERE (LOWER(nama_obat) LIKE LOWER(:drug_pattern) OR LOWER(nama_obat_internasional) LIKE LOWER(:drug_pattern))
                    AND is_active = 1
                    LIMIT 1
                """)
                
                result = connection.execute(search_query, {"drug_pattern": f"%{drug_name}%"})
                row = result.fetchone()
                
                if row:
                    validated_drugs.append(row[0])
                else:
                    validated_drugs.append(drug_name)  # Keep original if not found
        
        # Check for known interactions using pattern matching
        interactions = generate_interaction_warnings(validated_drugs)
        
        return {
            "input_drugs": drugs,
            "validated_drugs": validated_drugs,
            "interactions_found": len(interactions),
            "interactions": interactions,
            "analysis_source": "pattern_matching"
        }
        
    except Exception as e:
        print(f"Database error in check_drug_interactions: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/validate")
async def validate_drug_names(drug_names: str = Query(..., description="Comma-separated drug names to validate")):
    """Validate multiple drug names against database"""
    try:
        # Parse drug names
        drugs = [name.strip() for name in drug_names.split(",") if name.strip()]
        
        validation_results = []
        
        with engine.connect() as connection:
            for drug_name in drugs:
                # Search for drug
                search_query = text("""
                    SELECT id, nama_obat, nama_obat_internasional
                    FROM drugs 
                    WHERE (LOWER(nama_obat) LIKE LOWER(:drug_pattern) OR LOWER(nama_obat_internasional) LIKE LOWER(:drug_pattern))
                    AND is_active = 1
                    ORDER BY 
                        CASE 
                            WHEN LOWER(nama_obat) = LOWER(:exact_name) THEN 1
                            WHEN LOWER(nama_obat_internasional) = LOWER(:exact_name) THEN 2
                            WHEN LOWER(nama_obat) LIKE LOWER(:start_pattern) THEN 3
                            ELSE 4
                        END
                    LIMIT 3
                """)
                
                result = connection.execute(search_query, {
                    "drug_pattern": f"%{drug_name}%",
                    "exact_name": drug_name,
                    "start_pattern": f"{drug_name}%"
                })
                
                matches = []
                for row in result.fetchall():
                    matches.append({
                        "id": row[0],
                        "nama_obat": row[1],
                        "nama_obat_internasional": row[2]
                    })
                
                is_exact_match = False
                if matches:
                    first_match = matches[0]
                    is_exact_match = (
                        first_match["nama_obat"].lower() == drug_name.lower() or 
                        first_match["nama_obat_internasional"].lower() == drug_name.lower()
                    )
                
                validation_results.append({
                    "input_name": drug_name,
                    "is_valid": len(matches) > 0,
                    "exact_match": is_exact_match,
                    "matches": matches,
                    "best_match": matches[0] if matches else None,
                    "suggestions": matches
                })
        
        valid_count = sum(1 for r in validation_results if r["is_valid"])
        
        return {
            "total_drugs": len(drugs),
            "valid_drugs": valid_count,
            "invalid_drugs": len(drugs) - valid_count,
            "validation_results": validation_results
        }
        
    except Exception as e:
        print(f"Database error in validate_drug_names: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def generate_interaction_warnings(drug_names: List[str]) -> List[dict]:
    """Generate interaction warnings based on drug patterns"""
    interactions = []
    drug_names_lower = [name.lower() for name in drug_names]
    
    # Known interaction patterns
    interaction_patterns = [
        {
            "drugs": ["warfarin", "ibuprofen"],
            "severity": "Major",
            "description": "Increased bleeding risk with concurrent use",
            "recommendation": "Avoid concurrent use. Consider paracetamol as alternative.",
            "mechanism": "Warfarin anticoagulant effect enhanced by NSAID"
        },
        {
            "drugs": ["warfarin", "aspirin"],
            "severity": "Major",
            "description": "Significantly increased bleeding risk",
            "recommendation": "Avoid concurrent use unless closely monitored.",
            "mechanism": "Dual antiplatelet/anticoagulant effect"
        },
        {
            "drugs": ["clopidogrel", "omeprazole"],
            "severity": "Moderate", 
            "description": "Omeprazole may reduce effectiveness of Clopidogrel",
            "recommendation": "Consider alternative PPI (pantoprazole) or H2 blocker.",
            "mechanism": "CYP2C19 inhibition reduces clopidogrel activation"
        },
        {
            "drugs": ["simvastatin", "amlodipine"],
            "severity": "Moderate",
            "description": "Increased statin levels, risk of myopathy",
            "recommendation": "Limit simvastatin dose to 20mg daily.",
            "mechanism": "CYP3A4 inhibition increases statin exposure"
        },
        {
            "drugs": ["metformin", "furosemide"],
            "severity": "Moderate",
            "description": "Risk of lactic acidosis in dehydration",
            "recommendation": "Monitor kidney function and hydration status.",
            "mechanism": "Diuretic may worsen kidney function"
        }
    ]
    
    # Check each pattern
    for pattern in interaction_patterns:
        # Check if all drugs in pattern are present
        pattern_matches = []
        for pattern_drug in pattern["drugs"]:
            matching_input = None
            for input_drug in drug_names:
                if pattern_drug in input_drug.lower():
                    matching_input = input_drug
                    break
            
            if matching_input:
                pattern_matches.append(matching_input)
        
        # If we found matches for all drugs in the pattern
        if len(pattern_matches) == len(pattern["drugs"]):
            interactions.append({
                "drug_a": pattern_matches[0],
                "drug_b": pattern_matches[1],
                "severity": pattern["severity"],
                "description": pattern["description"],
                "recommendation": pattern["recommendation"],
                "mechanism": pattern["mechanism"],
                "pattern_matched": pattern["drugs"]
            })
    
    # Add category-based interactions (NSAIDs + anticoagulants, etc.)
    nsaids = ["ibuprofen", "diclofenac", "naproxen", "celecoxib", "meloxicam"]
    anticoagulants = ["warfarin", "heparin", "rivaroxaban", "apixaban", "dabigatran"]
    
    found_nsaid = None
    found_anticoag = None
    
    for drug in drug_names_lower:
        if not found_nsaid:
            for nsaid in nsaids:
                if nsaid in drug:
                    found_nsaid = next(d for d in drug_names if nsaid in d.lower())
                    break
        
        if not found_anticoag:
            for anticoag in anticoagulants:
                if anticoag in drug:
                    found_anticoag = next(d for d in drug_names if anticoag in d.lower())
                    break
    
    # Add generic NSAID-anticoagulant warning if not already covered
    if found_nsaid and found_anticoag:
        # Check if this interaction is not already in the list
        already_exists = any(
            (i["drug_a"] == found_nsaid and i["drug_b"] == found_anticoag) or
            (i["drug_a"] == found_anticoag and i["drug_b"] == found_nsaid)
            for i in interactions
        )
        
        if not already_exists:
            interactions.append({
                "drug_a": found_nsaid,
                "drug_b": found_anticoag,
                "severity": "Major",
                "description": "NSAIDs increase bleeding risk when used with anticoagulants",
                "recommendation": "Avoid concurrent use. Consider paracetamol for pain relief.",
                "mechanism": "Enhanced anticoagulant effect and GI bleeding risk",
                "interaction_type": "category_based"
            })
    
    return interactions