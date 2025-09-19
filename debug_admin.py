from app import app, db
from models import User


with app.app_context():
    users = User.query.all()
    print(f"users_count={len(users)}")
    for u in users:
        print(f"- id={u.id}, username={u.username}, email={u.email}, role={u.role}, active={u.is_active}")
    admin = User.query.filter_by(username='admin').first()
    if admin:
        hp = str(admin.password_hash)
        print(f"admin_hash_prefix={hp[:25]}")
    else:
        print("admin_not_found")



