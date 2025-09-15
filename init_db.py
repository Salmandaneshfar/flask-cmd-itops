from app import app, db, User

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ دیتابیس ساخته شد و کاربر admin اضافه شد.")
    else:
        print("ℹ️ کاربر admin از قبل وجود دارد.")

