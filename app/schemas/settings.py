from pydantic import BaseModel
from typing import Optional

# ==================== REVEAL CODE SCHEMAS ====================

class RevealCodeBase(BaseModel):
    code: str

class RevealCodeCreate(RevealCodeBase):
    pass

class RevealCodeUpdate(RevealCodeBase):
    pass

class RevealCodeVerify(RevealCodeBase):
    pass

class RevealCodeResponse(BaseModel):
    id: int
    key: str
    value: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

# ==================== DAILY ATTENDANCE SCHEMAS ====================

class DailyAttendanceBase(BaseModel):
    departement: Optional[str] = None
    tanggal: Optional[str] = None  # format YYYY-MM-DD
    k_GMT_1: Optional[int] = 0
    k_GMT_2: Optional[int] = 0
    os_GMT_1: Optional[int] = 0
    os_GMT_2: Optional[int] = 0

class DailyAttendanceCreate(DailyAttendanceBase):
    pass

class DailyAttendanceResponse(DailyAttendanceBase):
    id: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True