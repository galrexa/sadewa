# app/routers/patients.py
"""
API endpoints for patient management.

Handles CRUD operations for patients and provides pagination and search functionality.
Connects directly to the database without using separate models or schemas for simplicity.
"""
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

router = APIRouter()

# --- Database Connection Setup ---

def get_database_url() -> Optional[str]:
    """
    Retrieves the database URL from various environment variables or builds it.
    """
    db_url_vars = ['DATABASE_URL', 'MYSQL_URL', 'DB_URL', 'RAILWAY_MYSQL_URL']

    for var in db_url_vars:
        url = os.getenv(var)
        if url:
            # Clean URL: remove potential variable name prefix
            if '=' in url and url.startswith(var):
                url = url.split('=', 1)[1]
            # Ensure the correct driver is used for SQLAlchemy
            if url.startswith('mysql://'):
                url = url.replace('mysql://', 'mysql+pymysql://')
            print(f"✅ Using database URL from {var}: {url[:50]}...")
            return url

    # Fallback: build URL from individual components
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '3306')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    database = os.getenv('DB_NAME', 'sadewa_db')

    url = f"mysql+pymysql://{user}:{password or ''}@{host}:{port}/{database}"
    print(f"🔧 Built database URL from components: {url[:50]}...")
    return url

DATABASE_URL = get_database_url()
if not DATABASE_URL:
    raise RuntimeError("Database configuration not found. Please set DATABASE_URL.")

try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for debugging SQL queries
        pool_pre_ping=True,
        pool_recycle=300
    )
    print("✅ Database engine created successfully")
except SQLAlchemyError as e:
    print(f"❌ Failed to create database engine: {e}")
    engine = None # Ensure engine is None if creation fails
    raise

def get_db():
    """
    FastAPI dependency to get a database connection.
    Yields a connection from the engine's connection pool.
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Database service is unavailable")

    connection = None
    try:
        connection = engine.connect()
        yield connection
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}") from e
    finally:
        if connection:
            connection.close()

# --- API Endpoints ---

@router.get("/patients")
async def get_all_patients(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Number of patients per page"),
    search: Optional[str] = Query(None, description="Search by name, ID, or phone"),
    db: Session = Depends(get_db)
):
    """
    Get all patients with pagination and search functionality.
    """
    try:
        offset = (page - 1) * limit
        base_query = "SELECT id, name, age, gender, weight_kg, phone FROM patients"
        count_query = "SELECT COUNT(*) as total FROM patients"

        where_clause = ""
        params = {}

        if search:
            where_clause = "WHERE name LIKE :search OR id = :search_id OR phone LIKE :search"
            params["search"] = f"%{search}%"
            try:
                params["search_id"] = int(search)
            except ValueError:
                params["search_id"] = -1 # Impossible ID to prevent SQL errors

        total_query = text(count_query + where_clause)
        total_result = db.execute(total_query, params)
        total = total_result.scalar_one_or_none() or 0

        data_query_str = f"{base_query} {where_clause} ORDER BY id ASC LIMIT :limit OFFSET :offset"
        data_query = text(data_query_str)
        params.update({"limit": limit, "offset": offset})

        data_result = db.execute(data_query, params)
        patients = data_result.mappings().all()

        patients_list = [
            {
                "id": f"P{str(p['id']).zfill(3)}",
                "database_id": p['id'],
                "name": p['name'],
                "age": p['age'],
                "gender": p['gender'],
                "weight_kg": float(p['weight_kg']) if p['weight_kg'] is not None else None,
                "phone": p['phone']
            } for p in patients
        ]

        total_pages = (total + limit - 1) // limit
        return {
            "patients": patients_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e


@router.get("/patients/{patient_id}")
async def get_patient_by_id(patient_id: str, db: Session = Depends(get_db)):
    """
    Get a specific patient by ID. Accepts 'P001' format or a numeric string.
    """
    try:
        if patient_id.startswith('P'):
            numeric_id = int(patient_id[1:])
        else:
            numeric_id = int(patient_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid patient ID format") from exc

    try:
        query = text("SELECT id, name, age, gender, weight_kg, phone FROM patients WHERE id = :patient_id")
        result = db.execute(query, {"patient_id": numeric_id})
        patient = result.mappings().one_or_none()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        return {
            "id": f"P{str(patient['id']).zfill(3)}",
            "database_id": patient['id'],
            "name": patient['name'],
            "age": patient['age'],
            "gender": patient['gender'],
            "weight_kg": float(patient['weight_kg']) if patient['weight_kg'] is not None else None,
            "phone": patient['phone']
        }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e


@router.post("/patients", status_code=201)
async def create_patient(patient_data: dict, db: Session = Depends(get_db)):
    """
    Create a new patient. The ID is auto-incremented by the database.
    """
    required_fields = ["name", "age", "gender"]
    if not all(field in patient_data for field in required_fields):
        raise HTTPException(status_code=400, detail="Missing required fields: name, age, gender")
    if patient_data.get("gender") not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be 'male' or 'female'")

    try:
        insert_query = text(
            "INSERT INTO patients (name, age, gender, weight_kg, phone) "
            "VALUES (:name, :age, :gender, :weight_kg, :phone)"
        )
        params = {
            "name": patient_data["name"],
            "age": patient_data["age"],
            "gender": patient_data["gender"],
            "weight_kg": patient_data.get("weight_kg"),
            "phone": patient_data.get("phone")
        }
        result = db.execute(insert_query, params)
        db.commit()
        new_id = result.lastrowid
        return await get_patient_by_id(str(new_id), db)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {e}") from e


@router.put("/patients/{patient_id}")
async def update_patient(patient_id: str, patient_data: dict, db: Session = Depends(get_db)):
    """
    Update an existing patient's details.
    """
    try:
        if patient_id.startswith('P'):
            numeric_id = int(patient_id[1:])
        else:
            numeric_id = int(patient_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid patient ID format") from exc

    # First, verify the patient exists to provide a 404 if not.
    await get_patient_by_id(patient_id, db)

    update_fields = []
    params = {"patient_id": numeric_id}
    allowed_fields = ["name", "age", "gender", "weight_kg", "phone"]

    for field in allowed_fields:
        if field in patient_data:
            if field == "gender" and patient_data[field] not in ["male", "female"]:
                raise HTTPException(status_code=400, detail="Gender must be 'male' or 'female'")
            update_fields.append(f"{field} = :{field}")
            params[field] = patient_data[field]

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    try:
        update_query = text(f"UPDATE patients SET {', '.join(update_fields)} WHERE id = :patient_id")
        db.execute(update_query, params)
        db.commit()
        return await get_patient_by_id(patient_id, db)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update patient: {e}") from e


@router.delete("/patients/{patient_id}", status_code=200)
async def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """
    Delete a patient from the database.
    """
    try:
        if patient_id.startswith('P'):
            numeric_id = int(patient_id[1:])
        else:
            numeric_id = int(patient_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid patient ID format") from exc

    # Verify the patient exists before attempting to delete.
    await get_patient_by_id(patient_id, db)

    try:
        delete_query = text("DELETE FROM patients WHERE id = :patient_id")
        result = db.execute(delete_query, {"patient_id": numeric_id})
        db.commit()
        if result.rowcount == 0:
            # This case is unlikely due to the check above but is a good safeguard.
            raise HTTPException(status_code=404, detail="Patient not found during delete operation")
        return {"message": f"Patient {patient_id} deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete patient: {e}") from e


@router.get("/patients/")
async def get_patients_legacy(db: Session = Depends(get_db)):
    """
    Legacy endpoint that returns a flat array of patients for frontend compatibility.
    """
    try:
        result = await get_all_patients(page=1, limit=100, db=db)
        return result["patients"]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e