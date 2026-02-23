from sqlalchemy import String, Numeric, Integer, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from .base import Base


class Salary(Base):
    __tablename__ = "salaries"
    __table_args__ = (UniqueConstraint("nik", "periode", name="uq_salary_nik_periode"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nik: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    periode: Mapped[date] = mapped_column(Date, nullable=False)
    gaji_pokok: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    tunj_berkala: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    tunj_jabatan: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    tunj_kerajinan: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    tunj_pph21: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    uang_shift: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    uang_makan: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    ins_prod: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    bonus_skill: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    ins_hadir: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    kompensasi_cuti: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    lainnya1: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    lainnya2: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    lainnya3: Mapped[float] = mapped_column(Numeric(10,2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)