import pyodbc
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from app.models.hr import Employee
from app.services.settings import get_setting
import logging

logger = logging.getLogger(__name__)

def _get_nik_list_by_time_range(db: Session, target_date: date, start_time: time, end_time: time) -> list:
    """
    Helper untuk mengambil daftar NIK (Badgenumber) yang check-in antara start_time dan end_time pada target_date.
    """
    start_dt = datetime.combine(target_date, start_time)
    end_dt = datetime.combine(target_date, end_time)

    mdb_path = get_setting(db, "mdb_path", "Q:\\att2026.mdb")

    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={mdb_path};"
        r"Mode=Read;"
    )
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT u.Badgenumber
            FROM USERINFO u
            INNER JOIN CHECKINOUT c ON u.USERID = c.USERID
            WHERE c.CHECKTIME >= ? AND c.CHECKTIME < ?
        """
        cursor.execute(query, (start_dt, end_dt))
        rows = cursor.fetchall()
        badge_numbers = [str(row[0]) for row in rows if row[0] is not None]
        cursor.close()
        conn.close()

        if badge_numbers:
            employees = db.query(Employee.nik).filter(Employee.nik.in_(badge_numbers)).all()
            return [emp.nik for emp in employees]
        return []
    except Exception as e:
        logger.error(f"Error membaca MDB: {e}")
        return []

def get_checkin_nik_list_today(db: Session) -> list:
    """Mengembalikan daftar NIK yang check-in hari ini (06:30 - 07:03)."""
    return _get_nik_list_by_time_range(db, date.today(), time(6, 30), time(7, 3))

def get_checkin_count_today(db: Session) -> int:
    """Menghitung jumlah karyawan yang check-in hari ini."""
    return len(get_checkin_nik_list_today(db))

def get_checkout_nik_list_today(db: Session) -> list:
    """Mengembalikan daftar NIK yang check-out hari ini (17:00 - 17:30)."""
    return _get_nik_list_by_time_range(db, date.today(), time(17, 0), time(17, 30))

def get_checkout_count_today(db: Session) -> int:
    """Menghitung jumlah karyawan yang check-out hari ini."""
    return len(get_checkout_nik_list_today(db))

def get_checkin_details_today(db: Session) -> list:
    """
    Mengembalikan daftar lengkap karyawan yang check-in hari ini beserta jam check-in.
    """
    target_date = date.today()
    start_dt = datetime.combine(target_date, time(6, 30))
    end_dt = datetime.combine(target_date, time(7, 3))

    mdb_path = get_setting(db, "mdb_path", "Q:\\att2026.mdb")

    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={mdb_path};"
        r"Mode=Read;"
    )
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            SELECT u.Badgenumber, c.CHECKTIME
            FROM USERINFO u
            INNER JOIN CHECKINOUT c ON u.USERID = c.USERID
            WHERE c.CHECKTIME >= ? AND c.CHECKTIME < ?
            ORDER BY c.CHECKTIME
        """
        cursor.execute(query, (start_dt, end_dt))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        result = []
        for badge, check_time in rows:
            badge_str = str(badge)
            employee = db.query(Employee).filter(Employee.nik == badge_str).first()
            if employee:
                result.append({
                    "id": employee.id,
                    "nik": employee.nik,
                    "nama": employee.nama,
                    "dept": employee.dept,
                    "jabatan": employee.jabatan,
                    "jam": check_time.strftime("%H:%M:%S") if check_time else None
                })
        return result
    except Exception as e:
        logger.error(f"Error membaca MDB untuk detail: {e}")
        return []