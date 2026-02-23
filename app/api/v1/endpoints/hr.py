from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from datetime import datetime
from typing import List, Optional

from app.core.dependencies import get_db, require_roles
from app.schemas.user import UserRole
from app.schemas.hr import EmployeeResponse, EmployeeCreate, EmployeeUpdate
from app.services import hr as hr_service
from app.services import checkin as checkin_service
from app.models.salary import Salary
from app.models.hr import Employee
from app.models.auth import User

router = APIRouter(prefix="/hr", tags=["HR"])

@router.get("/employees")
def read_employees(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    sort_by: str = 'nik',
    sort_desc: bool = False,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    employees, total = hr_service.get_employees_paginated(
        db, skip=skip, limit=limit, search=search, sort_by=sort_by, sort_desc=sort_desc, active_only=active_only
    )
    items = [EmployeeResponse.model_validate(emp) for emp in employees]
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    return hr_service.get_employee_stats(db)

@router.get("/pimpinan-detail")
def get_pimpinan_detail(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    return hr_service.get_pimpinan_detail(db)

@router.get("/employees/export")
def export_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    excel_data = hr_service.export_employees_to_excel(db)
    if excel_data is None:
        raise HTTPException(status_code=404, detail="No employees found")
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employees.xlsx"}
    )

@router.post("/employees/import")
async def import_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format")
    contents = await file.read()
    result = await hr_service.import_employees_from_excel(db, contents)
    return result

@router.get("/employees/{employee_id}/with-salary")
def get_employee_with_latest_salary(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    employee = hr_service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    salaries = db.query(Salary).filter(Salary.nik == employee.nik).order_by(Salary.periode.desc()).all()
    
    current_salary = None
    start_periode = None
    if salaries:
        salary_data = []
        for sal in salaries:
            total = (
                (sal.gaji_pokok or 0) +
                (sal.tunj_berkala or 0) +
                (sal.tunj_jabatan or 0) +
                (sal.tunj_kerajinan or 0) +
                (sal.tunj_pph21 or 0) +
                (sal.uang_shift or 0) +
                (sal.uang_makan or 0) +
                (sal.ins_prod or 0) +
                (sal.bonus_skill or 0) +
                (sal.ins_hadir or 0) +
                (sal.kompensasi_cuti or 0) +
                (sal.lainnya1 or 0) +
                (sal.lainnya2 or 0) +
                (sal.lainnya3 or 0)
            )
            salary_data.append((sal.periode, total))
        latest_periode, current_salary = salary_data[0]
        start_periode = min([periode for periode, total in salary_data if total == current_salary]).strftime("%Y-%m")

    # Format tanggal
    tgl_rekrut = employee.tgl_rekrut.strftime("%Y-%m-%d") if employee.tgl_rekrut else None
    tgl_out = employee.tgl_out.strftime("%Y-%m-%d") if employee.tgl_out else None

    return {
        "id": employee.id,
        "nik": employee.nik,
        "nama": employee.nama,
        "dept": employee.dept,
        "jabatan": employee.jabatan,
        "foto": employee.foto,
        "tgl_rekrut": tgl_rekrut,
        "tgl_out": tgl_out,
        "current_salary": current_salary,
        "start_periode": start_periode
    }

@router.get("/employees/{employee_id}/salaries")
def get_employee_salaries(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    employee = hr_service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    salaries = db.query(Salary).filter(Salary.nik == employee.nik).order_by(Salary.periode.asc()).all()
    
    if not salaries:
        return {"items": [], "total": 0, "stats_per_periode": []}
    
    filtered = []
    last_total = None
    for sal in salaries:
        total = (
            (sal.gaji_pokok or 0) +
            (sal.tunj_berkala or 0) +
            (sal.tunj_jabatan or 0) +
            (sal.tunj_kerajinan or 0) +
            (sal.tunj_pph21 or 0) +
            (sal.uang_shift or 0) +
            (sal.uang_makan or 0) +
            (sal.ins_prod or 0) +
            (sal.bonus_skill or 0) +
            (sal.ins_hadir or 0) +
            (sal.kompensasi_cuti or 0) +
            (sal.lainnya1 or 0) +
            (sal.lainnya2 or 0) +
            (sal.lainnya3 or 0)
        )
        if total != last_total:
            filtered.append({
                "id": sal.id,
                "periode": sal.periode,
                "total": total,
            })
            last_total = total
    
    for i in range(1, len(filtered)):
        prev_total = filtered[i-1]["total"]
        curr_total = filtered[i]["total"]
        increase_amount = curr_total - prev_total
        increase_percent = (increase_amount / prev_total * 100) if prev_total != 0 else 0
        filtered[i]["increase_amount"] = increase_amount
        filtered[i]["increase_percent"] = round(increase_percent, 2)
    
    if filtered:
        filtered[0]["increase_amount"] = None
        filtered[0]["increase_percent"] = None
    
    stats_per_periode = []
    if employee.jabatan:
        jabatan_lower = employee.jabatan.lower()
        if 'manager' in jabatan_lower:
            pattern = '%manager%'
        elif 'supervisor' in jabatan_lower:
            pattern = '%supervisor%'
        elif 'leader' in jabatan_lower:
            pattern = '%leader%'
        else:
            pattern = employee.jabatan
        
        same_job_employees = db.query(Employee).filter(
            Employee.jabatan.ilike(pattern),
            Employee.tgl_out == None
        ).all()
        niks = [emp.nik for emp in same_job_employees]
        
        all_salaries = db.query(Salary).filter(Salary.nik.in_(niks)).all()
        
        salaries_by_periode = {}
        for sal in all_salaries:
            total = (
                (sal.gaji_pokok or 0) +
                (sal.tunj_berkala or 0) +
                (sal.tunj_jabatan or 0) +
                (sal.tunj_kerajinan or 0) +
                (sal.tunj_pph21 or 0) +
                (sal.uang_shift or 0) +
                (sal.uang_makan or 0) +
                (sal.ins_prod or 0) +
                (sal.bonus_skill or 0) +
                (sal.ins_hadir or 0) +
                (sal.kompensasi_cuti or 0) +
                (sal.lainnya1 or 0) +
                (sal.lainnya2 or 0) +
                (sal.lainnya3 or 0)
            )
            periode_str = sal.periode.strftime("%Y-%m")
            if periode_str not in salaries_by_periode:
                salaries_by_periode[periode_str] = []
            salaries_by_periode[periode_str].append(total)
        
        for item in filtered:
            periode_str = item["periode"].strftime("%Y-%m")
            totals = salaries_by_periode.get(periode_str, [])
            if totals:
                stats_per_periode.append({
                    "periode": periode_str,
                    "min": min(totals),
                    "max": max(totals),
                    "avg": sum(totals) / len(totals)
                })
            else:
                stats_per_periode.append({
                    "periode": periode_str,
                    "min": None,
                    "max": None,
                    "avg": None
                })
    
    for item in filtered:
        item["periode"] = item["periode"].strftime("%Y-%m")
    
    filtered_desc = list(reversed(filtered))
    stats_per_periode_desc = list(reversed(stats_per_periode))
    
    return {
        "items": filtered_desc,
        "total": len(filtered_desc),
        "stats_per_periode": stats_per_periode_desc
    }

@router.post("/employees/{employee_id}/upload-foto")
async def upload_employee_foto(
    employee_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    employee = hr_service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    foto_path = hr_service.save_photo_from_upload(file, employee.nik)
    if not foto_path:
        raise HTTPException(status_code=500, detail="Failed to save photo")
    
    employee.foto = foto_path
    db.commit()
    
    return {"foto_url": f"/static/{foto_path}"}

@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
def read_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    employee = hr_service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    return hr_service.create_employee(db, employee)

@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    return hr_service.update_employee(db, employee_id, employee)

@router.delete("/employees/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    return hr_service.delete_employee(db, employee_id)

# ==================== ENDPOINT CHECK-IN/OUT ====================

@router.get("/checkin/count", response_model=int)
def get_checkin_count_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    """Jumlah karyawan yang check-in hari ini (06:30-07:03)."""
    return checkin_service.get_checkin_count_today(db)

@router.get("/checkin/niks", response_model=List[str])
def get_checkin_niks_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    """Daftar NIK karyawan yang check-in hari ini."""
    return checkin_service.get_checkin_nik_list_today(db)

@router.get("/checkin/details")
def get_checkin_details_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    """Daftar lengkap karyawan yang check-in hari ini beserta jam check-in."""
    return checkin_service.get_checkin_details_today(db)

@router.get("/checkout/count", response_model=int)
def get_checkout_count_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    """Jumlah karyawan yang check-out hari ini (17:00-17:30)."""
    return checkin_service.get_checkout_count_today(db)

@router.get("/checkout/niks", response_model=List[str])
def get_checkout_niks_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    """Daftar NIK karyawan yang check-out hari ini."""
    return checkin_service.get_checkout_nik_list_today(db)