import openpyxl
from io import BytesIO
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.attendance import DailyAttendance
import logging

logger = logging.getLogger(__name__)

async def import_attendance_from_excel(db: Session, file_content: bytes) -> dict:
    """
    Import data daily attendance dari file Excel
    Format kolom: departement, tanggal, k_gmt_1, k_gmt_2, os_gmt_1, os_gmt_2
    """
    try:
        workbook = openpyxl.load_workbook(BytesIO(file_content))
        sheet = workbook.active
        
        inserted = 0
        skipped = 0
        errors = []
        
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            try:
                if not any(row):
                    continue
                
                departement = str(row[0]) if row[0] else None
                tanggal = row[1]
                k_gmt_1 = int(row[2]) if row[2] not in (None, '') else 0
                k_gmt_2 = int(row[3]) if row[3] not in (None, '') else 0
                os_gmt_1 = int(row[4]) if row[4] not in (None, '') else 0
                os_gmt_2 = int(row[5]) if row[5] not in (None, '') else 0
                
                # Parse tanggal
                if isinstance(tanggal, str):
                    try:
                        tanggal = datetime.strptime(tanggal, "%Y-%m-%d").date()
                    except:
                        tanggal = datetime.strptime(tanggal, "%d/%m/%Y").date()
                elif isinstance(tanggal, datetime):
                    tanggal = tanggal.date()
                
                attendance = DailyAttendance(
                    departement=departement,
                    tanggal=tanggal,
                    k_gmt_1=k_gmt_1,
                    k_gmt_2=k_gmt_2,
                    os_gmt_1=os_gmt_1,
                    os_gmt_2=os_gmt_2
                )
                db.add(attendance)
                inserted += 1
                
            except Exception as e:
                skipped += 1
                errors.append({"row": row_idx, "error": str(e)})
        
        db.commit()
        
        return {
            "success": True,
            "inserted": inserted,
            "skipped": skipped,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error importing attendance: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal membaca file Excel: {str(e)}")

def export_attendance_to_excel(db: Session) -> bytes:
    """Export semua data daily attendance ke Excel"""
    try:
        attendances = db.query(DailyAttendance).order_by(DailyAttendance.tanggal.desc()).all()
        
        if not attendances:
            return None
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Daily Attendance"
        
        headers = ["Departement", "Tanggal", "k_GMT_1", "k_GMT_2", "os_GMT_1", "os_GMT_2"]
        ws.append(headers)
        
        for att in attendances:
            ws.append([
                att.departement,
                att.tanggal.strftime("%Y-%m-%d") if att.tanggal else "",
                att.k_gmt_1,
                att.k_gmt_2,
                att.os_gmt_1,
                att.os_gmt_2
            ])
        
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return excel_file.getvalue()
        
    except Exception as e:
        logger.error(f"Error exporting attendance: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal export: {str(e)}")

def get_attendance_comparison(db: Session, date1: str, date2: str):
    """
    Membandingkan data attendance antara dua tanggal.
    Mengembalikan list per departemen dengan nilai masing-masing komponen dan total.
    """
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d").date()
        d2 = datetime.strptime(date2, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Format tanggal harus YYYY-MM-DD")

    # Ambil data untuk tanggal 1
    data1 = db.query(
        DailyAttendance.departement,
        func.sum(DailyAttendance.k_gmt_1).label('k1'),
        func.sum(DailyAttendance.k_gmt_2).label('k2'),
        func.sum(DailyAttendance.os_gmt_1).label('o1'),
        func.sum(DailyAttendance.os_gmt_2).label('o2')
    ).filter(DailyAttendance.tanggal == d1).group_by(DailyAttendance.departement).all()

    # Ambil data untuk tanggal 2
    data2 = db.query(
        DailyAttendance.departement,
        func.sum(DailyAttendance.k_gmt_1).label('k1'),
        func.sum(DailyAttendance.k_gmt_2).label('k2'),
        func.sum(DailyAttendance.os_gmt_1).label('o1'),
        func.sum(DailyAttendance.os_gmt_2).label('o2')
    ).filter(DailyAttendance.tanggal == d2).group_by(DailyAttendance.departement).all()

    # Gabungkan dalam dictionary
    dict1 = {d.departement: d for d in data1}
    dict2 = {d.departement: d for d in data2}
    all_depts = set(dict1.keys()) | set(dict2.keys())
    result = []
    for dept in sorted(all_depts):
        d1 = dict1.get(dept)
        d2 = dict2.get(dept)
        row = {
            "departement": dept,
            "tgl1": {
                "k_gmt_1": d1.k1 if d1 else 0,
                "k_gmt_2": d1.k2 if d1 else 0,
                "os_gmt_1": d1.o1 if d1 else 0,
                "os_gmt_2": d1.o2 if d1 else 0,
                "total": (d1.k1 if d1 else 0) + (d1.k2 if d1 else 0) + (d1.o1 if d1 else 0) + (d1.o2 if d1 else 0)
            },
            "tgl2": {
                "k_gmt_1": d2.k1 if d2 else 0,
                "k_gmt_2": d2.k2 if d2 else 0,
                "os_gmt_1": d2.o1 if d2 else 0,
                "os_gmt_2": d2.o2 if d2 else 0,
                "total": (d2.k1 if d2 else 0) + (d2.k2 if d2 else 0) + (d2.o1 if d2 else 0) + (d2.o2 if d2 else 0)
            }
        }
        result.append(row)
    return result

def get_latest_two_dates(db: Session, offset: int = 0):
    """
    Mengembalikan dua tanggal terakhir yang tersedia di tabel,
    berdasarkan offset. offset=0 -> dua terbaru, offset=1 -> dua setelahnya, dst.
    Returns (date1, date2) dengan date1 lebih lama, date2 lebih baru.
    Jika tidak cukup data, raise HTTPException.
    """
    # Ambil semua tanggal unik, urut descending
    dates = db.query(DailyAttendance.tanggal).distinct().order_by(DailyAttendance.tanggal.desc()).all()
    dates = [d[0] for d in dates]
    
    if len(dates) < 2:
        raise HTTPException(status_code=404, detail="Data attendance tidak mencukupi untuk perbandingan")
    
    if offset < 0 or offset > len(dates) - 2:
        raise HTTPException(status_code=404, detail="Offset di luar jangkauan")
    
    date2 = dates[offset]      # lebih baru
    date1 = dates[offset + 1]  # lebih lama
    return date1, date2

def get_attendance_comparison(db: Session, date1: str, date2: str):
    """
    Membandingkan data attendance antara dua tanggal.
    Mengembalikan dict dengan dates dan data per departemen.
    """
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d").date()
        d2 = datetime.strptime(date2, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Format tanggal harus YYYY-MM-DD")

    # Ambil data untuk tanggal 1
    data1 = db.query(
        DailyAttendance.departement,
        func.sum(DailyAttendance.k_gmt_1).label('k1'),
        func.sum(DailyAttendance.k_gmt_2).label('k2'),
        func.sum(DailyAttendance.os_gmt_1).label('o1'),
        func.sum(DailyAttendance.os_gmt_2).label('o2')
    ).filter(DailyAttendance.tanggal == d1).group_by(DailyAttendance.departement).all()

    # Ambil data untuk tanggal 2
    data2 = db.query(
        DailyAttendance.departement,
        func.sum(DailyAttendance.k_gmt_1).label('k1'),
        func.sum(DailyAttendance.k_gmt_2).label('k2'),
        func.sum(DailyAttendance.os_gmt_1).label('o1'),
        func.sum(DailyAttendance.os_gmt_2).label('o2')
    ).filter(DailyAttendance.tanggal == d2).group_by(DailyAttendance.departement).all()

    # Gabungkan dalam dictionary
    dict1 = {d.departement: d for d in data1}
    dict2 = {d.departement: d for d in data2}
    all_depts = set(dict1.keys()) | set(dict2.keys())
    result = []
    for dept in sorted(all_depts):
        d1 = dict1.get(dept)
        d2 = dict2.get(dept)
        row = {
            "departement": dept,
            "tgl1": {
                "k_gmt_1": d1.k1 if d1 else 0,
                "k_gmt_2": d1.k2 if d1 else 0,
                "os_gmt_1": d1.o1 if d1 else 0,
                "os_gmt_2": d1.o2 if d1 else 0,
                "total": (d1.k1 if d1 else 0) + (d1.k2 if d1 else 0) + (d1.o1 if d1 else 0) + (d1.o2 if d1 else 0)
            },
            "tgl2": {
                "k_gmt_1": d2.k1 if d2 else 0,
                "k_gmt_2": d2.k2 if d2 else 0,
                "os_gmt_1": d2.o1 if d2 else 0,
                "os_gmt_2": d2.o2 if d2 else 0,
                "total": (d2.k1 if d2 else 0) + (d2.k2 if d2 else 0) + (d2.o1 if d2 else 0) + (d2.o2 if d2 else 0)
            }
        }
        result.append(row)
    
    return {
        "dates": [date1, date2],
        "data": result
    }