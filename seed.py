from app.core.database import SessionLocal
from app.models.auth import User
from app.schemas.user import UserRole  # <-- GANTI INI
from app.core.security import get_password_hash

def seed():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role=UserRole.SUPERADMIN.value,  # Ambil .value
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✅ User superadmin berhasil dibuat.")
        else:
            print("ℹ️ User admin sudah ada.")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()