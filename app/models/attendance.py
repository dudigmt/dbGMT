from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class DailyAttendance(Base):
    __tablename__ = "daily_attendance"

    id = Column(Integer, primary_key=True, index=True)
    departement = Column(String(100))
    tanggal = Column(Date)
    k_gmt_1 = Column(Integer, default=0)   # <-- pakai huruf kecil
    k_gmt_2 = Column(Integer, default=0)   # <-- pakai huruf kecil
    os_gmt_1 = Column(Integer, default=0)  # <-- pakai huruf kecil
    os_gmt_2 = Column(Integer, default=0)  # <-- pakai huruf kecil
    created_at = Column(DateTime(timezone=True), server_default=func.now())