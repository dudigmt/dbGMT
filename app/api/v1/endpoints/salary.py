from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
from app.core.dependencies import get_db, require_roles
from app.schemas.user import UserRole
from app.schemas.salary import SalaryResponse, SalaryCreate, SalaryUpdate
from app.services import salary as salary_service

PAGINATION_MAX_LIMIT = 500
router = APIRouter(prefix="/salaries", tags=["Salaries"])

@router.get("/", response_model=List[SalaryResponse])
def read_salaries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS]))
):
    skip = max(0, skip)
    limit = min(max(1, limit), PAGINATION_MAX_LIMIT)
    return salary_service.get_salaries(db, skip=skip, limit=limit)

@router.get("/export")
def export_salaries(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    excel_data = salary_service.export_salaries_to_excel(db)
    if excel_data is None:
        raise HTTPException(status_code=404, detail="No salaries found")
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=salaries.xlsx"}
    )

@router.post("/import")
async def import_salaries(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format")
    contents = await file.read()
    result = await salary_service.import_salaries_from_excel(db, contents)
    return result

@router.get("/{salary_id}", response_model=SalaryResponse)
def read_salary(
    salary_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS]))
):
    salary = salary_service.get_salary(db, salary_id)
    if not salary:
        raise HTTPException(status_code=404, detail="Salary not found")
    return salary

@router.post("/", response_model=SalaryResponse, status_code=status.HTTP_201_CREATED)
def create_salary(
    salary: SalaryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    return salary_service.create_salary(db, salary)

@router.put("/{salary_id}", response_model=SalaryResponse)
def update_salary(
    salary_id: int,
    salary: SalaryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN]))
):
    return salary_service.update_salary(db, salary_id, salary)

@router.delete("/{salary_id}")
def delete_salary(
    salary_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN]))
):
    return salary_service.delete_salary(db, salary_id)