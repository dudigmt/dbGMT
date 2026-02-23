from sqlalchemy.orm import Session
from app.models.settings import Settings
from fastapi import HTTPException, status

def get_setting(db: Session, key: str, default: str = None) -> str | None:
    """Mendapatkan nilai setting berdasarkan key. Jika tidak ada, kembalikan default."""
    setting = db.query(Settings).filter(Settings.key == key).first()
    return setting.value if setting else default

def set_setting(db: Session, key: str, value: str):
    """Menyimpan atau memperbarui setting."""
    setting = db.query(Settings).filter(Settings.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = Settings(key=key, value=value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting

def verify_reveal_code(db: Session, code: str) -> bool:
    """Memverifikasi kode reveal. Default '1234'."""
    stored_code = get_setting(db, "reveal_code", "1234")
    return code == stored_code

def update_reveal_code(db: Session, new_code: str, current_user):
    """Mengubah kode reveal. Hanya untuk superadmin."""
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya superadmin yang dapat mengubah kode reveal"
        )
    set_setting(db, "reveal_code", new_code)
    return {"message": "Kode reveal berhasil diperbarui"}

def get_reveal_code(db: Session) -> str:
    """Mengembalikan kode reveal saat ini (untuk keperluan superadmin)."""
    return get_setting(db, "reveal_code", "1234")

# ==================== FUNGSI UNTUK MDB PATH ====================

def get_mdb_path(db: Session) -> str:
    """Mengembalikan path file MDB yang tersimpan, atau default jika belum ada."""
    return get_setting(db, "mdb_path", "Q:\\att2026.mdb")

def update_mdb_path(db: Session, new_path: str, current_user):
    """Mengubah path MDB. Hanya untuk superadmin."""
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya superadmin yang dapat mengubah path MDB"
        )
    set_setting(db, "mdb_path", new_path)
    return {"message": "Path MDB berhasil diperbarui", "path": new_path}