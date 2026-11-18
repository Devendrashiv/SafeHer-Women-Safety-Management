from werkzeug.security import generate_password_hash
from app import get_db
from datetime import datetime
import getpass

print("Create SafeHer administrator")
name = input("Admin name: ").strip()
email = input("Admin email: ").strip().lower()
password = getpass.getpass("Password (minimum 8 characters): ")
if not name or not email or len(password) < 8:
    raise SystemExit("Name, email and a password of at least 8 characters are required.")
try:
    with get_db() as db:
        db.execute(
            "INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
            (name, email, generate_password_hash(password), "admin", datetime.now().isoformat(timespec="seconds"))
        )
    print("Admin created. Sign in at /login.")
except Exception as exc:
    print("Could not create admin:", exc)
