from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional

class SalaryBase(BaseModel):
    nik: str = Field(..., max_length=20)
    periode: date
    gaji_pokok: Optional[float] = None
    tunj_berkala: Optional[float] = None
    tunj_jabatan: Optional[float] = None
    tunj_kerajinan: Optional[float] = None
    tunj_pph21: Optional[float] = None
    uang_shift: Optional[float] = None
    uang_makan: Optional[float] = None
    ins_prod: Optional[float] = None
    bonus_skill: Optional[float] = None
    ins_hadir: Optional[float] = None
    kompensasi_cuti: Optional[float] = None
    lainnya1: Optional[float] = None
    lainnya2: Optional[float] = None
    lainnya3: Optional[float] = None

class SalaryCreate(SalaryBase):
    pass

class SalaryUpdate(BaseModel):
    nik: Optional[str] = Field(None, max_length=20)
    periode: Optional[date] = None
    gaji_pokok: Optional[float] = None
    tunj_berkala: Optional[float] = None
    tunj_jabatan: Optional[float] = None
    tunj_kerajinan: Optional[float] = None
    tunj_pph21: Optional[float] = None
    uang_shift: Optional[float] = None
    uang_makan: Optional[float] = None
    ins_prod: Optional[float] = None
    bonus_skill: Optional[float] = None
    ins_hadir: Optional[float] = None
    kompensasi_cuti: Optional[float] = None
    lainnya1: Optional[float] = None
    lainnya2: Optional[float] = None
    lainnya3: Optional[float] = None

class SalaryResponse(SalaryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)