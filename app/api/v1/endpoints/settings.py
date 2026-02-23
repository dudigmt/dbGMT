from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from typing import Optional

from app.core.dependencies import get_db, require_roles
from app.schemas.user import UserRole
from app.schemas.settings import RevealCodeUpdate, RevealCodeVerify, RevealCodeResponse
from app.services import settings as settings_service
from app.services import attendance as attendance_service
from app.models.auth import User

router = APIRouter(prefix="/settings", tags=["Settings"])

# ==================== REVEAL CODE ENDPOINTS ====================

@router.get("/reveal-code", response_model=RevealCodeResponse)
def get_reveal_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    """Mendapatkan kode reveal saat ini (hanya untuk superadmin)"""
    from app.models.settings import Settings
    setting = db.query(Settings).filter(Settings.key == "reveal_code").first()
    if not setting:
        # Buat default
        setting = settings_service.set_setting(db, "reveal_code", "1234")
    return {"id": setting.id, "key": setting.key, "value": setting.value}

@router.put("/reveal-code", response_model=RevealCodeResponse)
def update_reveal_code(
    data: RevealCodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    """Mengupdate kode reveal (hanya superadmin)"""
    result = settings_service.update_reveal_code(db, data.code, current_user)
    from app.models.settings import Settings
    setting = db.query(Settings).filter(Settings.key == "reveal_code").first()
    return {"id": setting.id, "key": setting.key, "value": setting.value}

@router.post("/verify-reveal-code")
def verify_reveal_code(
    data: RevealCodeVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    """Verifikasi kode reveal untuk melihat gaji"""
    is_valid = settings_service.verify_reveal_code(db, data.code)
    return {"valid": is_valid}

# ==================== MDB PATH ENDPOINTS ====================

@router.get("/mdb-path")
def get_mdb_path(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    """Mendapatkan path file MDB yang tersimpan"""
    path = settings_service.get_mdb_path(db)
    return {"path": path}

@router.put("/mdb-path")
def update_mdb_path(
    path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    """Mengupdate path file MDB"""
    result = settings_service.update_mdb_path(db, path, current_user)
    return result

@router.post("/mdb-path/test")
def test_mdb_connection(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    """Test koneksi ke file MDB dengan path yang diberikan"""
    path = data.get("path")
    if not path:
        path = settings_service.get_mdb_path(db)
    try:
        import pyodbc
        conn_str = (
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            f"DBQ={path};"
        )
        conn = pyodbc.connect(conn_str)
        conn.close()
        return {"success": True, "message": "Koneksi berhasil"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==================== DAILY ATTENDANCE ENDPOINTS ====================

@router.post("/attendance/import")
async def import_attendance(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File harus format Excel")
    contents = await file.read()
    result = await attendance_service.import_attendance_from_excel(db, contents)
    return result

@router.get("/attendance/export")
def export_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    excel_data = attendance_service.export_attendance_to_excel(db)
    if excel_data is None:
        raise HTTPException(status_code=404, detail="Tidak ada data attendance")
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=daily_attendance.xlsx"}
    )

@router.get("/attendance/preview")
def preview_attendance(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN]))
):
    from app.models.attendance import DailyAttendance
    attendances = db.query(DailyAttendance).order_by(
        DailyAttendance.tanggal.desc(),
        DailyAttendance.id.desc()
    ).limit(limit).all()
    
    result = []
    for att in attendances:
        result.append({
            "id": att.id,
            "departement": att.departement,
            "tanggal": att.tanggal.isoformat() if att.tanggal else None,
            "k_gmt_1": att.k_gmt_1,
            "k_gmt_2": att.k_gmt_2,
            "os_gmt_1": att.os_gmt_1,
            "os_gmt_2": att.os_gmt_2,
            "created_at": att.created_at.isoformat() if att.created_at else None
        })
    return result

@router.get("/attendance/compare")
def compare_attendance(
    date1: str = Query(..., description="Tanggal pertama (YYYY-MM-DD)"),
    date2: str = Query(..., description="Tanggal kedua (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS]))
):
    """Membandingkan data attendance antara dua tanggal"""
    return attendance_service.get_attendance_comparison(db, date1, date2)

@router.get("/attendance/compare-latest")
def compare_latest_attendance(
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.BOSS, UserRole.USER]))
):
    """Membandingkan dua tanggal terakhir dengan offset tertentu (0 = dua terbaru)"""
    date1, date2 = attendance_service.get_latest_two_dates(db, offset)
    return attendance_service.get_attendance_comparison(db, date1.isoformat(), date2.isoformat())