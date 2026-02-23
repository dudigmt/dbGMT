import io
import pandas as pd
from sqlalchemy.orm import Session
from app.models.salary import Salary
from app.schemas.salary import SalaryCreate, SalaryUpdate
from app.utils.excel_io import normalize_excel_columns, ensure_required_columns, row_dicts_with_index
from fastapi import HTTPException, status
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

# All numeric components used to compute total salary (single source of truth)
SALARY_TOTAL_FIELDS = [
    "gaji_pokok", "tunj_berkala", "tunj_jabatan", "tunj_kerajinan", "tunj_pph21",
    "uang_shift", "uang_makan", "ins_prod", "bonus_skill", "ins_hadir",
    "kompensasi_cuti", "lainnya1", "lainnya2", "lainnya3",
]


def salary_total(salary_obj) -> float:
    """Compute total salary from a Salary model instance or dict-like row. Single place for formula."""
    total = 0.0
    for field in SALARY_TOTAL_FIELDS:
        val = getattr(salary_obj, field, None) if hasattr(salary_obj, field) else (salary_obj.get(field) if isinstance(salary_obj, dict) else None)
        total += float(val or 0)
    return total


# ==================== CRUD DASAR ====================

def get_salaries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Salary).offset(skip).limit(limit).all()

def get_all_salaries(db: Session):
    return db.query(Salary).all()

def get_salary(db: Session, salary_id: int):
    return db.query(Salary).filter(Salary.id == salary_id).first()

def get_salary_by_nik_periode(db: Session, nik: str, periode: date):
    return db.query(Salary).filter(Salary.nik == nik, Salary.periode == periode).first()

def create_salary(db: Session, salary: SalaryCreate):
    # Cek duplikat NIK + Periode
    existing = get_salary_by_nik_periode(db, salary.nik, salary.periode)
    if existing:
        raise HTTPException(status_code=400, detail="Data gaji untuk NIK dan periode ini sudah ada")
    
    db_salary = Salary(**salary.model_dump())
    db.add(db_salary)
    try:
        db.commit()
        db.refresh(db_salary)
        return db_salary
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Gagal menyimpan data")

def update_salary(db: Session, salary_id: int, salary: SalaryUpdate):
    db_salary = get_salary(db, salary_id)
    if not db_salary:
        raise HTTPException(status_code=404, detail="Data gaji tidak ditemukan")
    
    update_data = salary.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_salary, key, value)
    
    try:
        db.commit()
        db.refresh(db_salary)
        return db_salary
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengupdate data")

def delete_salary(db: Session, salary_id: int):
    db_salary = get_salary(db, salary_id)
    if not db_salary:
        raise HTTPException(status_code=404, detail="Data gaji tidak ditemukan")
    db.delete(db_salary)
    try:
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Gagal menghapus data")

# ==================== EXPORT ====================

def export_salaries_to_excel(db: Session):
    salaries = get_all_salaries(db)
    if not salaries:
        return None
    data = [
        {
            "nik": sal.nik,
            "periode": sal.periode.strftime("%Y-%m"),
            **{f: getattr(sal, f) for f in SALARY_TOTAL_FIELDS},
        }
        for sal in salaries
    ]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Salaries')
    output.seek(0)
    return output.getvalue()

# ==================== IMPORT ====================

async def import_salaries_from_excel(db: Session, file_content: bytes):
    try:
        df = pd.read_excel(io.BytesIO(file_content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File Excel tidak valid: {str(e)}")

    df = normalize_excel_columns(df)
    logger.info(f"Kolom terdeteksi: {list(df.columns)}")

    required = ["nik", "periode"]
    missing = ensure_required_columns(df, required)
    if missing:
        raise HTTPException(status_code=400, detail=f"Kolom wajib tidak ada: {missing}")

    df = df.dropna(subset=["nik", "periode"])

    if "nik" in df.columns:
        df["nik"] = df["nik"].astype(str).replace("nan", None).replace("None", None)
        df["nik"] = df["nik"].str.replace(r"\.0$", "", regex=True)

    df["periode"] = pd.to_datetime(df["periode"], errors="coerce").dt.date
    df = df.dropna(subset=["periode"])

    for col in SALARY_TOTAL_FIELDS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    existing_keys = {(row.nik, row.periode) for row in db.query(Salary.nik, Salary.periode).all()}
    salaries_to_insert = []
    errors = []
    skipped = 0

    for row_num, clean in row_dicts_with_index(df, start_row=2):
        try:
            salary_data = SalaryCreate(**clean)
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})
            continue

        key = (salary_data.nik, salary_data.periode)
        if key in existing_keys:
            skipped += 1
            continue

        salaries_to_insert.append(Salary(**salary_data.model_dump()))
        existing_keys.add(key)

    if errors:
        return {"success": False, "errors": errors}
    if not salaries_to_insert:
        return {"success": True, "inserted": 0, "skipped": skipped}
    try:
        db.bulk_save_objects(salaries_to_insert)
        db.commit()
        return {"success": True, "inserted": len(salaries_to_insert), "skipped": skipped}
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk insert error: {e}")
        raise HTTPException(status_code=500, detail="Gagal import data")