"""
ICD-10 router dengan database integration
Menggunakan table icds yang sudah ada dengan 10,469 records
"""
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ICD10
from app.schemas import ICD10Result

router = APIRouter()


@router.get("/search", response_model=List[ICD10Result])
async def search_icd10(
    q: str = Query(..., min_length=2, description="Query pencarian diagnosis"),
    limit: int = Query(10, ge=1, le=50, description="Limit hasil pencarian"),
    db: Session = Depends(get_db)
):
    """
    Search ICD-10 diagnosis dari database

    Pencarian dilakukan pada:
    - Kode ICD-10 (code)
    - Nama diagnosis bahasa Indonesia (name_id)
    - Nama diagnosis bahasa Inggris (name_en)
    """
    start_time = time.time()

    try:
        # Query dengan LIKE search pada semua field
        search_pattern = f"%{q.lower()}%"

        results = db.query(ICD10).filter(
            or_(
                func.lower(ICD10.code).like(search_pattern),
                func.lower(ICD10.name_id).like(search_pattern),
                func.lower(ICD10.name_en).like(search_pattern)
            )
        ).limit(limit).all()

        # Convert ke response format
        icd_results = []
        for result in results:
            icd_results.append(ICD10Result(
                code=result.code,
                name_id=result.name_id,
                name_en=result.name_en
            ))

        processing_time = time.time() - start_time

        # Log successful search
        print(f"✅ ICD-10 search '{q}' returned {len(icd_results)} results in {processing_time:.3f}s")

        return icd_results

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ ICD-10 search failed for '{q}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        ) from e


@router.get("/code/{icd_code}", response_model=ICD10Result)
async def get_icd10_by_code(
    icd_code: str,
    db: Session = Depends(get_db)
):
    """
    Get specific ICD-10 diagnosis by code
    """
    try:
        result = db.query(ICD10).filter(ICD10.code == icd_code.upper()).first()

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"ICD-10 code '{icd_code}' not found"
            )

        return ICD10Result(
            code=result.code,
            name_id=result.name_id,
            name_en=result.name_en
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving ICD-10 code: {str(e)}"
        ) from e


@router.get("/stats")
async def get_icd10_statistics(db: Session = Depends(get_db)):
    """
    Get ICD-10 database statistics
    """
    try:
        total_codes = db.query(func.count(ICD10.code)).scalar()

        # Sample beberapa codes untuk verification
        sample_codes = db.query(ICD10).limit(5).all()

        return {
            "total_icd10_codes": total_codes,
            "database_status": "active",
            "sample_codes": [
                {
                    "code": code.code,
                    "name_id": (code.name_id[:100] + "..."
                                if len(code.name_id) > 100 else code.name_id)
                } for code in sample_codes
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting ICD-10 statistics: {str(e)}"
        ) from e