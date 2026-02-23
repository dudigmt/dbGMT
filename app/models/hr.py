from sqlalchemy import String, Integer, Date, Float, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from .base import Base
import enum

# Enums (tetap sama)
class SexEnum(str, enum.Enum):
    L = "L"
    P = "P"

class StatusKawinEnum(str, enum.Enum):
    BELUM = "Belum Kawin"
    KAWIN = "Kawin"
    CERAI = "Cerai"

class GolDarahEnum(str, enum.Enum):
    A = "A"
    B = "B"
    AB = "AB"
    O = "O"

class StatusKaryawanEnum(str, enum.Enum):
    TETAP = "Tetap"
    KONTRAK = "Kontrak"
    OS = "OS"
    PROBATION = "Probation"
    MAGANG = "Magang"

class StatusKerjaEnum(str, enum.Enum):
    AKTIF = "Aktif"
    KELUAR = "Keluar"
    CUTI = "Cuti"

class StatusPajakEnum(str, enum.Enum):
    TK0 = "TK0"
    TK1 = "TK1"
    TK2 = "TK2"
    TK3 = "TK3"
    K0 = "K0"
    K1 = "K1"
    K2 = "K2"
    K3 = "K3"

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    nik: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # === Data Pribadi (15 kolom) ===
    nama: Mapped[str] = mapped_column(String(100), nullable=False)
    sex: Mapped[str] = mapped_column(String(1), nullable=False)
    tgl_lahir: Mapped[date] = mapped_column(Date, nullable=False)
    tempat_lahir: Mapped[str] = mapped_column(String(100), nullable=False)
    no_ktp: Mapped[str] = mapped_column(String(16), nullable=False)
    no_kk: Mapped[str] = mapped_column(String(16), nullable=True)
    no_hp: Mapped[str] = mapped_column(String(15), nullable=True)
    alamat: Mapped[str] = mapped_column(Text, nullable=True)
    kelurahan: Mapped[str] = mapped_column(String(100), nullable=True)
    kecamatan: Mapped[str] = mapped_column(String(100), nullable=True)
    kabupaten_kota: Mapped[str] = mapped_column(String(100), nullable=True)
    kode_pos: Mapped[str] = mapped_column(String(10), nullable=True)
    provinsi: Mapped[str] = mapped_column(String(100), nullable=True)
    status_kawin: Mapped[str] = mapped_column(String(20), nullable=True)
    tanggungan: Mapped[int] = mapped_column(Integer, default=0)
    agama: Mapped[str] = mapped_column(String(50), nullable=True)
    tinggi_badan: Mapped[float] = mapped_column(Float, nullable=True)
    berat_badan: Mapped[float] = mapped_column(Float, nullable=True)
    gol_darah: Mapped[str] = mapped_column(String(2), nullable=True)
    pendidikan: Mapped[str] = mapped_column(String(100), nullable=True)

    # === Data Kepegawaian (12 kolom) ===
    tgl_rekrut: Mapped[date] = mapped_column(Date, nullable=False)
    status_karyawan: Mapped[str] = mapped_column(String(20), nullable=True)
    tgl_kartetap: Mapped[date] = mapped_column(Date, nullable=True)
    posisi_karyawan: Mapped[str] = mapped_column(String(100), nullable=True)
    no_kartu_kpk: Mapped[str] = mapped_column(String(50), nullable=True)
    group: Mapped[str] = mapped_column(String(100), nullable=True)
    dept: Mapped[str] = mapped_column(String(100), nullable=True)
    jabatan: Mapped[str] = mapped_column(String(100), nullable=True)
    kontrak_ke: Mapped[int] = mapped_column(Integer, default=0)
    kontrak_berakhir: Mapped[date] = mapped_column(Date, nullable=True)
    kode_gaji: Mapped[str] = mapped_column(String(50), nullable=True)

    # === Data Bank & Pajak (11 kolom) ===
    no_rek_bank: Mapped[str] = mapped_column(String(30), nullable=True)
    kode_bank: Mapped[str] = mapped_column(String(10), nullable=True)
    nama_bank: Mapped[str] = mapped_column(String(100), nullable=True)
    status_ptkp: Mapped[str] = mapped_column(String(20), nullable=True)
    no_npwp: Mapped[str] = mapped_column(String(20), nullable=True)
    bpjs_tk: Mapped[bool] = mapped_column(Boolean, default=False)
    bpjs_tk_ditanggung: Mapped[str] = mapped_column(String(50), nullable=True)
    bpjs_tk_no: Mapped[str] = mapped_column(String(30), nullable=True)
    bpjs_kes: Mapped[bool] = mapped_column(Boolean, default=False)
    bpjs_kes_ditanggung: Mapped[str] = mapped_column(String(50), nullable=True)
    bpjs_kes_no: Mapped[str] = mapped_column(String(30), nullable=True)
    status_pajak: Mapped[str] = mapped_column(String(10), nullable=True)

    # === Data Lainnya (4 kolom) ===
    faskes: Mapped[str] = mapped_column(String(100), nullable=True)
    placement: Mapped[str] = mapped_column(String(100), nullable=True)
    tgl_out: Mapped[date] = mapped_column(Date, nullable=True)
    status_kerja: Mapped[str] = mapped_column(String(10), nullable=True, default="Aktif")
    foto: Mapped[str] = mapped_column(String(255), nullable=True)

    # === Timestamps (2 kolom) ===
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)