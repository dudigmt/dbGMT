from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional
from enum import Enum

# ==================== ENUMS (salin dari model) ====================
class SexEnum(str, Enum):
    L = "L"
    P = "P"

class StatusKawinEnum(str, Enum):
    BELUM = "Belum Kawin"
    KAWIN = "Kawin"
    CERAI = "Cerai"

class GolDarahEnum(str, Enum):
    A = "A"
    B = "B"
    AB = "AB"
    O = "O"

class StatusKaryawanEnum(str, Enum):
    TETAP = "Tetap"
    KONTRAK = "Kontrak"
    OS = "OS"
    PROBATION = "Probation"
    MAGANG = "Magang"

class StatusKerjaEnum(str, Enum):
    AKTIF = "Aktif"
    KELUAR = "Keluar"
    CUTI = "Cuti"

class StatusPajakEnum(str, Enum):
    TK0 = "TK0"
    TK1 = "TK1"
    TK2 = "TK2"
    TK3 = "TK3"
    K0 = "K0"
    K1 = "K1"
    K2 = "K2"
    K3 = "K3"

# ==================== EMPLOYEE SCHEMAS ====================
class EmployeeBase(BaseModel):
    nik: str = Field(..., max_length=20)
    nama: str = Field(..., max_length=100)
    sex: SexEnum
    tgl_lahir: date
    tempat_lahir: str = Field(..., max_length=100)
    no_ktp: str = Field(..., max_length=16)
    no_kk: Optional[str] = Field(None, max_length=16)
    no_hp: Optional[str] = Field(None, max_length=15)
    alamat: Optional[str] = None
    kelurahan: Optional[str] = Field(None, max_length=100)
    kecamatan: Optional[str] = Field(None, max_length=100)
    kabupaten_kota: Optional[str] = Field(None, max_length=100)
    kode_pos: Optional[str] = Field(None, max_length=10)
    provinsi: Optional[str] = Field(None, max_length=100)
    status_kawin: Optional[StatusKawinEnum] = None
    tanggungan: Optional[int] = 0
    agama: Optional[str] = Field(None, max_length=50)
    tinggi_badan: Optional[float] = None
    berat_badan: Optional[float] = None
    gol_darah: Optional[GolDarahEnum] = None
    pendidikan: Optional[str] = Field(None, max_length=100)
    tgl_rekrut: date
    status_karyawan: Optional[StatusKaryawanEnum] = None
    tgl_kartetap: Optional[date] = None
    posisi_karyawan: Optional[str] = Field(None, max_length=100)
    no_kartu_kpk: Optional[str] = Field(None, max_length=50)
    group: Optional[str] = Field(None, max_length=100)
    dept: Optional[str] = Field(None, max_length=100)
    jabatan: Optional[str] = Field(None, max_length=100)
    kontrak_ke: Optional[int] = 0
    kontrak_berakhir: Optional[date] = None
    kode_gaji: Optional[str] = Field(None, max_length=50)
    no_rek_bank: Optional[str] = Field(None, max_length=30)
    kode_bank: Optional[str] = Field(None, max_length=10)
    nama_bank: Optional[str] = Field(None, max_length=100)
    status_ptkp: Optional[str] = Field(None, max_length=20)
    no_npwp: Optional[str] = Field(None, max_length=20)
    bpjs_tk: Optional[bool] = False
    bpjs_tk_ditanggung: Optional[str] = Field(None, max_length=50)
    bpjs_tk_no: Optional[str] = Field(None, max_length=30)
    bpjs_kes: Optional[bool] = False
    bpjs_kes_ditanggung: Optional[str] = Field(None, max_length=50)
    bpjs_kes_no: Optional[str] = Field(None, max_length=30)
    status_pajak: Optional[StatusPajakEnum] = None
    faskes: Optional[str] = Field(None, max_length=100)
    placement: Optional[str] = Field(None, max_length=100)
    tgl_out: Optional[date] = None
    status_kerja: StatusKerjaEnum = StatusKerjaEnum.AKTIF
    foto: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    nik: Optional[str] = Field(None, max_length=20)
    nama: Optional[str] = Field(None, max_length=100)
    sex: Optional[SexEnum] = None
    tgl_lahir: Optional[date] = None
    tempat_lahir: Optional[str] = Field(None, max_length=100)
    no_ktp: Optional[str] = Field(None, max_length=16)
    no_kk: Optional[str] = Field(None, max_length=16)
    no_hp: Optional[str] = Field(None, max_length=15)
    alamat: Optional[str] = None
    kelurahan: Optional[str] = Field(None, max_length=100)
    kecamatan: Optional[str] = Field(None, max_length=100)
    kabupaten_kota: Optional[str] = Field(None, max_length=100)
    kode_pos: Optional[str] = Field(None, max_length=10)
    provinsi: Optional[str] = Field(None, max_length=100)
    status_kawin: Optional[StatusKawinEnum] = None
    tanggungan: Optional[int] = None
    agama: Optional[str] = Field(None, max_length=50)
    tinggi_badan: Optional[float] = None
    berat_badan: Optional[float] = None
    gol_darah: Optional[GolDarahEnum] = None
    pendidikan: Optional[str] = Field(None, max_length=100)
    tgl_rekrut: Optional[date] = None
    status_karyawan: Optional[StatusKaryawanEnum] = None
    tgl_kartetap: Optional[date] = None
    posisi_karyawan: Optional[str] = Field(None, max_length=100)
    no_kartu_kpk: Optional[str] = Field(None, max_length=50)
    group: Optional[str] = Field(None, max_length=100)
    dept: Optional[str] = Field(None, max_length=100)
    jabatan: Optional[str] = Field(None, max_length=100)
    kontrak_ke: Optional[int] = None
    kontrak_berakhir: Optional[date] = None
    kode_gaji: Optional[str] = Field(None, max_length=50)
    no_rek_bank: Optional[str] = Field(None, max_length=30)
    kode_bank: Optional[str] = Field(None, max_length=10)
    nama_bank: Optional[str] = Field(None, max_length=100)
    status_ptkp: Optional[str] = Field(None, max_length=20)
    no_npwp: Optional[str] = Field(None, max_length=20)
    bpjs_tk: Optional[bool] = None
    bpjs_tk_ditanggung: Optional[str] = Field(None, max_length=50)
    bpjs_tk_no: Optional[str] = Field(None, max_length=30)
    bpjs_kes: Optional[bool] = None
    bpjs_kes_ditanggung: Optional[str] = Field(None, max_length=50)
    bpjs_kes_no: Optional[str] = Field(None, max_length=30)
    status_pajak: Optional[StatusPajakEnum] = None
    faskes: Optional[str] = Field(None, max_length=100)
    placement: Optional[str] = Field(None, max_length=100)
    tgl_out: Optional[date] = None
    status_kerja: Optional[StatusKerjaEnum] = None
    foto: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)