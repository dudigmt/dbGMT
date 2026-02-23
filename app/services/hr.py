import io
import os
import uuid
import base64
import pandas as pd
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.models.hr import Employee
from app.models.salary import Salary
from app.schemas.hr import EmployeeCreate, EmployeeUpdate
from app.services import salary as salary_service
from app.utils.excel_io import normalize_excel_columns, ensure_required_columns, row_dicts_with_index
from app.utils.helpers import model_dump_for_db
from fastapi import HTTPException, status, UploadFile
import logging
from datetime import datetime, date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FUNGSI DASAR CRUD ====================

def get_all_employees(db: Session):
    return db.query(Employee).all()

def get_employee(db: Session, employee_id: int):
    return db.query(Employee).filter(Employee.id == employee_id).first()

def get_employee_by_nik(db: Session, nik: str):
    return db.query(Employee).filter(Employee.nik == nik).first()

def create_employee(db: Session, employee: EmployeeCreate):
    logger.info("=== Memulai proses create employee ===")
    logger.info(f"NIK: {employee.nik}, Nama: {employee.nama}")

    existing_nik = get_employee_by_nik(db, employee.nik)
    if existing_nik:
        logger.warning(f"NIK {employee.nik} sudah ada")
        raise HTTPException(status_code=400, detail="NIK already exists")

    data = model_dump_for_db(employee)
    db_emp = Employee(**data)
    db.add(db_emp)

    try:
        db.commit()
        db.refresh(db_emp)
        logger.info(f"Employee berhasil dibuat dengan ID: {db_emp.id}")
        return db_emp
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def update_employee(db: Session, employee_id: int, employee: EmployeeUpdate):
    db_emp = get_employee(db, employee_id)
    if not db_emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.nik is not None and employee.nik != db_emp.nik:
        existing_nik = get_employee_by_nik(db, employee.nik)
        if existing_nik:
            raise HTTPException(status_code=400, detail="NIK already exists")

    update_data = model_dump_for_db(employee, exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_emp, key, value)

    try:
        db.commit()
        db.refresh(db_emp)
        return db_emp
    except Exception as e:
        db.rollback()
        logger.error(f"Database error saat update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def delete_employee(db: Session, employee_id: int):
    db_emp = get_employee(db, employee_id)
    if not db_emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(db_emp)
    try:
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        logger.error(f"Database error saat delete: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== PAGINATION + SEARCH + SORT + FILTER AKTIF ====================

def get_employees_paginated(db: Session, skip: int = 0, limit: int = 100, search: str = None, sort_by: str = 'nik', sort_desc: bool = False, active_only: bool = True):
    query = db.query(Employee)
    
    if active_only:
        query = query.filter(Employee.tgl_out == None)
    
    if search:
        search_filter = (
            Employee.nik.ilike(f"%{search}%") |
            Employee.nama.ilike(f"%{search}%") |
            Employee.dept.ilike(f"%{search}%") |
            Employee.jabatan.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if sort_by == 'nik':
        query = query.order_by(Employee.nik.desc() if sort_desc else Employee.nik.asc())
    elif sort_by == 'nama':
        query = query.order_by(Employee.nama.desc() if sort_desc else Employee.nama.asc())
    elif sort_by == 'dept':
        if sort_desc:
            query = query.order_by(Employee.dept.desc().nullslast())
        else:
            query = query.order_by(Employee.dept.asc().nullsfirst())
    elif sort_by == 'jabatan':
        if sort_desc:
            query = query.order_by(Employee.jabatan.desc().nullslast())
        else:
            query = query.order_by(Employee.jabatan.asc().nullsfirst())
    elif sort_by == 'tgl_rekrut':
        query = query.order_by(Employee.tgl_rekrut.desc() if sort_desc else Employee.tgl_rekrut.asc())
    else:
        query = query.order_by(Employee.nik.asc())
    
    total = query.count()
    employees = query.offset(skip).limit(limit).all()
    return employees, total

# ==================== STATISTIK DASHBOARD (HANYA KARYAWAN AKTIF) ====================

def get_employee_stats(db: Session):
    """Single-query stats for active employees (tgl_out is null)."""
    row = (
        db.query(
            func.count(Employee.id).label("total_aktif"),
            func.sum(case((Employee.posisi_karyawan.ilike("%pimpinan%"), 1), else_=0)).label("pimpinan"),
            func.sum(case((Employee.posisi_karyawan.ilike("%karyawan%"), 1), else_=0)).label("karyawan"),
            func.sum(case((Employee.status_karyawan == "Tetap", 1), else_=0)).label("tetap"),
            func.sum(case((Employee.status_karyawan == "Kontrak", 1), else_=0)).label("kontrak"),
            func.sum(case((Employee.status_karyawan == "OS", 1), else_=0)).label("os"),
        )
        .filter(Employee.tgl_out.is_(None))
        .first()
    )
    return {
        "total_aktif": row.total_aktif or 0,
        "pimpinan": int(row.pimpinan or 0),
        "karyawan": int(row.karyawan or 0),
        "tetap": int(row.tetap or 0),
        "kontrak": int(row.kontrak or 0),
        "os": int(row.os or 0),
    }

# ==================== PIMPINAN DETAIL (HANYA AKTIF) ====================

def _pimpinan_to_dict(emp):
    return {"nik": emp.nik, "nama": emp.nama, "jabatan": emp.jabatan, "dept": emp.dept}


def get_pimpinan_detail(db: Session):
    """Single query for all Pimpinan (active), then group by jabatan in Python."""
    pimpinan_list = (
        db.query(Employee)
        .filter(Employee.posisi_karyawan == "Pimpinan", Employee.tgl_out.is_(None))
        .all()
    )
    manager, supervisor, leader = [], [], []
    for emp in pimpinan_list:
        jab = (emp.jabatan or "").lower()
        d = _pimpinan_to_dict(emp)
        if "manager" in jab or "jst" in jab:
            manager.append(d)
        elif "supervisor" in jab:
            supervisor.append(d)
        elif "leader" in jab:
            leader.append(d)
    return {"manager": manager, "supervisor": supervisor, "leader": leader}


# ==================== EMPLOYEE WITH LATEST SALARY ====================

def get_employee_with_latest_salary(db: Session, employee_id: int):
    """Return employee plus current_salary and start_periode from latest salary record(s)."""
    employee = get_employee(db, employee_id)
    if not employee:
        return None
    salaries = (
        db.query(Salary)
        .filter(Salary.nik == employee.nik)
        .order_by(Salary.periode.desc())
        .all()
    )
    if not salaries:
        return {
            "id": employee.id,
            "nik": employee.nik,
            "nama": employee.nama,
            "dept": employee.dept,
            "jabatan": employee.jabatan,
            "foto": employee.foto,
            "current_salary": None,
            "start_periode": None,
        }
    salary_data = [(sal.periode, salary_service.salary_total(sal)) for sal in salaries]
    latest_periode, current_salary = salary_data[0]
    start_periode = min(p for p, t in salary_data if t == current_salary)
    return {
        "id": employee.id,
        "nik": employee.nik,
        "nama": employee.nama,
        "dept": employee.dept,
        "jabatan": employee.jabatan,
        "foto": employee.foto,
        "current_salary": current_salary,
        "start_periode": start_periode.strftime("%Y-%m"),
    }


# ==================== FUNGSI UPLOAD FOTO ====================

def save_photo_from_upload(file: UploadFile, nik: str) -> str | None:
    """
    Menyimpan file foto dari UploadFile ke folder uploads.
    Mengembalikan path relatif (misal: 'uploads/20260218_123456_abc.jpg')
    """
    try:
        # Validasi tipe file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Baca konten file
        contents = file.file.read()
        
        # Validasi ukuran file (maks 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Ukuran file maksimal 10MB")
        
        # Tentukan ekstensi dari filename
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            ext = '.jpg'  # default
        
        # Buat nama file unik: NIK_timestamp_uuid.ext
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        filename = f"{nik}_{timestamp}_{unique_id}{ext}"
        
        # Path folder uploads
        upload_folder = os.path.join('app', 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        
        # Simpan file
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Kembalikan path relatif
        return f"uploads/{filename}"
    except Exception as e:
        logger.error(f"Gagal menyimpan foto dari upload: {e}")
        return None

def save_photo_from_base64(base64_string: str, nik: str) -> str | None:
    """
    Menyimpan foto base64 ke folder uploads.
    Mengembalikan path relatif.
    """
    if not base64_string:
        return None
    try:
        if "," in base64_string:
            header, data = base64_string.split(",", 1)
        else:
            header, data = "", base64_string

        file_data = base64.b64decode(data)

        # Validasi ukuran file (maks 10MB)
        if len(file_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Ukuran file maksimal 10MB")

        ext = "jpg"
        if header and ";" in header:
            mime = header.split(';')[0].split('/')[-1]
            ext = mime if mime in ['jpg', 'jpeg', 'png', 'gif'] else 'jpg'
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        filename = f"{nik}_{timestamp}_{unique_id}.{ext}"
        
        upload_folder = os.path.join('app', 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return f"uploads/{filename}"
    except Exception as e:
        logger.error(f"Gagal menyimpan foto dari base64: {e}")
        return None

# ==================== EXPORT EXCEL ====================

def export_employees_to_excel(db: Session):
    employees = get_all_employees(db)
    if not employees:
        return None

    data = []
    for emp in employees:
        emp_dict = {
            "nik": emp.nik,
            "nama": emp.nama,
            "sex": emp.sex,
            "tgl_lahir": emp.tgl_lahir,
            "tempat_lahir": emp.tempat_lahir,
            "no_ktp": emp.no_ktp,
            "no_kk": emp.no_kk,
            "no_hp": emp.no_hp,
            "alamat": emp.alamat,
            "kelurahan": emp.kelurahan,
            "kecamatan": emp.kecamatan,
            "kabupaten_kota": emp.kabupaten_kota,
            "kode_pos": emp.kode_pos,
            "provinsi": emp.provinsi,
            "status_kawin": emp.status_kawin,
            "tanggungan": emp.tanggungan,
            "agama": emp.agama,
            "tinggi_badan": emp.tinggi_badan,
            "berat_badan": emp.berat_badan,
            "gol_darah": emp.gol_darah,
            "pendidikan": emp.pendidikan,
            "tgl_rekrut": emp.tgl_rekrut,
            "status_karyawan": emp.status_karyawan,
            "tgl_kartetap": emp.tgl_kartetap,
            "posisi_karyawan": emp.posisi_karyawan,
            "no_kartu_kpk": emp.no_kartu_kpk,
            "group": emp.group,
            "dept": emp.dept,
            "jabatan": emp.jabatan,
            "kontrak_ke": emp.kontrak_ke,
            "kontrak_berakhir": emp.kontrak_berakhir,
            "kode_gaji": emp.kode_gaji,
            "no_rek_bank": emp.no_rek_bank,
            "kode_bank": emp.kode_bank,
            "nama_bank": emp.nama_bank,
            "status_ptkp": emp.status_ptkp,
            "no_npwp": emp.no_npwp,
            "bpjs_tk": "Ya" if emp.bpjs_tk else "Tidak",
            "bpjs_tk_ditanggung": emp.bpjs_tk_ditanggung,
            "bpjs_tk_no": emp.bpjs_tk_no,
            "bpjs_kes": "Ya" if emp.bpjs_kes else "Tidak",
            "bpjs_kes_ditanggung": emp.bpjs_kes_ditanggung,
            "bpjs_kes_no": emp.bpjs_kes_no,
            "status_pajak": emp.status_pajak,
            "faskes": emp.faskes,
            "placement": emp.placement,
            "tgl_out": emp.tgl_out,
            "status_kerja": emp.status_kerja,
            "foto": emp.foto,
        }
        data.append(emp_dict)

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Karyawan')
    output.seek(0)
    return output.getvalue()

# ==================== IMPORT EXCEL ====================

async def import_employees_from_excel(db: Session, file_content: bytes):
    try:
        df = pd.read_excel(io.BytesIO(file_content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")

    df = normalize_excel_columns(df)
    logger.info(f"Normalized columns: {list(df.columns)}")

    required_columns = ["nik", "nama", "sex", "tgl_lahir", "tempat_lahir", "no_ktp", "tgl_rekrut"]
    missing = ensure_required_columns(df, required_columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    df = df.dropna(subset=['nik', 'no_ktp'])

    string_cols = [
        'nik', 'no_ktp', 'no_kk', 'no_hp', 'tempat_lahir', 'kelurahan', 'kecamatan',
        'kabupaten_kota', 'kode_pos', 'provinsi', 'agama', 'pendidikan', 'posisi_karyawan',
        'no_kartu_kpk', 'group', 'dept', 'jabatan', 'kode_gaji', 'no_rek_bank',
        'kode_bank', 'nama_bank', 'status_ptkp', 'no_npwp',
        'bpjs_tk_ditanggung', 'bpjs_tk_no', 'bpjs_kes_ditanggung', 'bpjs_kes_no',
        'faskes', 'placement', 'foto'
    ]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', None).replace('None', None)

    numeric_id_fields = ['no_kk', 'no_rek_bank', 'no_npwp', 'bpjs_tk_no', 'bpjs_kes_no', 'no_ktp']
    for col in numeric_id_fields:
        if col in df.columns:
            df[col] = df[col].str.replace(r'\.0$', '', regex=True)

    date_cols = ['tgl_lahir', 'tgl_rekrut', 'tgl_kartetap', 'kontrak_berakhir', 'tgl_out']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

    df = df.dropna(subset=['tgl_lahir', 'tempat_lahir'])

    numeric_cols = ['tanggungan', 'tinggi_badan', 'berat_badan', 'kontrak_ke']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    bool_cols = ['bpjs_tk', 'bpjs_kes']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({'Ya': True, 'Tidak': False, '': None})

    if 'status_kawin' in df.columns:
        df['status_kawin'] = df['status_kawin'].replace({'Tidak Kawin': 'Belum Kawin'})

    valid_pajak = ['TK0', 'TK1', 'TK2', 'TK3', 'K0', 'K1', 'K2', 'K3']
    if 'status_pajak' in df.columns:
        df['status_pajak'] = df['status_pajak'].apply(lambda x: x if x in valid_pajak else None)

    if 'status_kerja' in df.columns:
        df['status_kerja'] = df['status_kerja'].fillna('Aktif')
    else:
        df['status_kerja'] = 'Aktif'

    if 'status_karyawan' not in df.columns:
        df['status_karyawan'] = None
    else:
        df['status_karyawan'] = df['status_karyawan'].where(df['status_karyawan'].notna(), None)

    existing_niks = {nik for (nik,) in db.query(Employee.nik).all()}
    employees_to_insert = []
    errors = []
    skipped = 0

    for row_num, clean in row_dicts_with_index(df, start_row=2):
        try:
            emp_data = EmployeeCreate(**clean)
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})
            continue

        if emp_data.nik in existing_niks:
            skipped += 1
            continue

        data = model_dump_for_db(emp_data)
        employees_to_insert.append(Employee(**data))
        existing_niks.add(emp_data.nik)

    if errors:
        return {"success": False, "errors": errors}
    if not employees_to_insert:
        return {"success": True, "inserted": 0, "skipped": skipped}
    try:
        db.bulk_save_objects(employees_to_insert)
        db.commit()
        return {"success": True, "inserted": len(employees_to_insert), "skipped": skipped}
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk insert error: {e}")
        raise HTTPException(status_code=500, detail="Database error during bulk insert")