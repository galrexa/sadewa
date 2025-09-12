# app/routers/drugs.py - Fixed untuk table structure yang ada
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.database import get_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/drugs/search")
async def search_drugs(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search drugs by name (Indonesian or International)
    Simple search untuk data Fornas
    """
    try:
        logger.info(f"Searching drugs with query: '{q}', limit: {limit}")
        
        # Simple search query untuk table structure yang ada
        search_query = text("""
            SELECT 
                id,
                nama_obat,
                nama_obat_internasional,
                CONCAT(nama_obat, ' (', nama_obat_internasional, ')') as display_name
            FROM drugs 
            WHERE is_active = TRUE 
            AND (
                nama_obat LIKE :like_term
                OR nama_obat_internasional LIKE :like_term
            )
            ORDER BY 
                CASE 
                    WHEN nama_obat LIKE :exact_term THEN 1
                    WHEN nama_obat_internasional LIKE :exact_term THEN 2
                    WHEN nama_obat LIKE :start_term THEN 3
                    WHEN nama_obat_internasional LIKE :start_term THEN 4
                    ELSE 5
                END,
                nama_obat ASC
            LIMIT :limit_val
        """)
        
        result = db.execute(search_query, {
            'like_term': f'%{q}%',
            'exact_term': q,
            'start_term': f'{q}%',
            'limit_val': limit
        })
        
        drugs = []
        for row in result:
            drugs.append({
                "id": row[0],
                "nama_obat": row[1],
                "nama_obat_internasional": row[2],
                "display_name": row[3]
            })
        
        logger.info(f"Found {len(drugs)} drugs matching query '{q}'")
        return drugs
        
    except Exception as e:
        logger.error(f"Error searching drugs: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/drugs/{drug_id}")
async def get_drug_by_id(drug_id: int, db: Session = Depends(get_db)):
    """Get drug information by ID"""
    try:
        query = text("""
            SELECT 
                id, nama_obat, nama_obat_internasional, is_active, created_at
            FROM drugs 
            WHERE id = :drug_id AND is_active = TRUE
        """)
        
        result = db.execute(query, {'drug_id': drug_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Drug with ID {drug_id} not found")
        
        return {
            "id": result[0],
            "nama_obat": result[1],
            "nama_obat_internasional": result[2],
            "is_active": result[3],
            "created_at": result[4]
        }
        
    except Exception as e:
        logger.error(f"Error getting drug {drug_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/drugs/check-interactions")
async def check_simple_interactions(
    drug_names: str = Query(..., description="Comma-separated drug names"),
    db: Session = Depends(get_db)
):
    """
    Check for simple drug interactions
    Input: comma-separated drug names
    """
    try:
        drug_list = [name.strip() for name in drug_names.split(',')]
        
        if len(drug_list) < 2:
            raise HTTPException(status_code=400, detail="At least 2 drugs required for interaction check")
        
        logger.info(f"Checking interactions for drugs: {drug_list}")
        
        interactions = []
        
        # Check all combinations
        for i in range(len(drug_list)):
            for j in range(i + 1, len(drug_list)):
                drug_a = drug_list[i].lower()
                drug_b = drug_list[j].lower()
                
                # Check both directions (drug_a with drug_b and drug_b with drug_a)
                try:
                    query = text("""
                        SELECT 
                            drug_a, drug_b, severity, description, recommendation
                        FROM simple_drug_interactions 
                        WHERE is_active = TRUE
                        AND (
                            (LOWER(drug_a) LIKE :drug_a AND LOWER(drug_b) LIKE :drug_b)
                            OR (LOWER(drug_a) LIKE :drug_b AND LOWER(drug_b) LIKE :drug_a)
                        )
                    """)
                    
                    result = db.execute(query, {
                        'drug_a': f'%{drug_a}%',
                        'drug_b': f'%{drug_b}%'
                    }).fetchone()
                    
                    if result:
                        interactions.append({
                            "drug_a": result[0],
                            "drug_b": result[1],
                            "severity": result[2],
                            "description": result[3],
                            "recommendation": result[4],
                            "input_drugs": [drug_list[i], drug_list[j]]
                        })
                except Exception as table_error:
                    # Table simple_drug_interactions mungkin belum ada
                    logger.warning(f"Simple interactions table not available: {table_error}")
                    break
        
        logger.info(f"Found {len(interactions)} interactions")
        
        return {
            "input_drugs": drug_list,
            "interactions_found": len(interactions),
            "interactions": interactions
        }
        
    except Exception as e:
        logger.error(f"Error checking drug interactions: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/drugs/stats")
async def get_drug_stats(db: Session = Depends(get_db)):
    """Get database statistics for drugs"""
    try:
        stats_query = text("""
            SELECT COUNT(*) as total_drugs FROM drugs WHERE is_active = TRUE
        """)
        
        result = db.execute(stats_query).fetchone()
        total_drugs = result[0] if result else 0
        
        # Try to get interactions count (table might not exist)
        interactions_count = 0
        try:
            interactions_query = text("""
                SELECT COUNT(*) as total_interactions FROM simple_drug_interactions WHERE is_active = TRUE
            """)
            interactions_result = db.execute(interactions_query).fetchone()
            interactions_count = interactions_result[0] if interactions_result else 0
        except Exception:
            logger.info("Simple interactions table not available")
        
        # Sample obat terbaru
        sample_query = text("""
            SELECT nama_obat, nama_obat_internasional 
            FROM drugs 
            WHERE is_active = TRUE 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        sample_result = db.execute(sample_query)
        sample_drugs = []
        for row in sample_result:
            sample_drugs.append({
                "nama_obat": row[0],
                "nama_obat_internasional": row[1]
            })
        
        return {
            "total_drugs": total_drugs,
            "total_interactions": interactions_count,
            "sample_drugs": sample_drugs,
            "database_status": "connected",
            "last_updated": "2024-09-11"
        }
        
    except Exception as e:
        logger.error(f"Error getting drug stats: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/drugs/autocomplete")
async def autocomplete_drugs(
    q: str = Query(..., min_length=1, description="Search query for autocomplete"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """
    Autocomplete untuk drug names - untuk medication input component
    """
    try:
        query = text("""
            SELECT DISTINCT
                nama_obat_internasional as suggestion
            FROM drugs 
            WHERE is_active = TRUE 
            AND nama_obat_internasional LIKE :term
            ORDER BY 
                CASE WHEN nama_obat_internasional LIKE :exact_term THEN 1 ELSE 2 END,
                LENGTH(nama_obat_internasional) ASC,
                nama_obat_internasional ASC
            LIMIT :limit_val
        """)
        
        result = db.execute(query, {
            'term': f'%{q}%',
            'exact_term': f'{q}%',
            'limit_val': limit
        })
        
        suggestions = [row[0] for row in result]
        
        return {
            "query": q,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error in autocomplete: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Add manual interaction for testing (optional)
@router.post("/drugs/add-interaction")
async def add_manual_interaction(
    drug_a: str,
    drug_b: str,
    severity: str,
    description: str,
    recommendation: str = None,
    db: Session = Depends(get_db)
):
    """
    Tambah interaksi obat manual untuk testing
    Hanya untuk development/testing
    """
    try:
        # Check if simple_drug_interactions table exists
        check_table = text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'simple_drug_interactions'
        """)
        
        table_exists = db.execute(check_table).fetchone()[0] > 0
        
        if not table_exists:
            # Create table if not exists
            create_table = text("""
                CREATE TABLE simple_drug_interactions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    drug_a VARCHAR(255) NOT NULL,
                    drug_b VARCHAR(255) NOT NULL,
                    severity ENUM('Major', 'Moderate', 'Minor') NOT NULL,
                    description TEXT NOT NULL,
                    recommendation TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    INDEX idx_drug_a (drug_a),
                    INDEX idx_drug_b (drug_b),
                    INDEX idx_severity (severity),
                    
                    UNIQUE KEY unique_simple_interaction (drug_a, drug_b)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            db.execute(create_table)
            db.commit()
            logger.info("Created simple_drug_interactions table")
        
        insert_query = text("""
            INSERT INTO simple_drug_interactions 
            (drug_a, drug_b, severity, description, recommendation, is_active)
            VALUES (:drug_a, :drug_b, :severity, :description, :recommendation, TRUE)
        """)
        
        db.execute(insert_query, {
            'drug_a': drug_a,
            'drug_b': drug_b,
            'severity': severity,
            'description': description,
            'recommendation': recommendation or "Monitor closely"
        })
        
        db.commit()
        
        return {
            "message": "Interaction added successfully",
            "drug_a": drug_a,
            "drug_b": drug_b,
            "severity": severity
        }
        
    except Exception as e:
        logger.error(f"Error adding interaction: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")