from pydantic import BaseModel
from typing import Optional

class DailyAttendanceBase(BaseModel):
    departement: Optional[str] = None
    tanggal: Optional[str] = None  # format YYYY-MM-DD
    k_gmt_1: Optional[int] = 0     # <-- konsisten huruf kecil
    k_gmt_2: Optional[int] = 0
    os_gmt_1: Optional[int] = 0
    os_gmt_2: Optional[int] = 0

class DailyAttendanceCreate(DailyAttendanceBase):
    pass

class DailyAttendanceResponse(DailyAttendanceBase):
    id: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True