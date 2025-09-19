from app import app, db
from models import User
from sqlalchemy import or_
from werkzeug.security import check_password_hash


def reset_admin_password(new_password: str) -> None:
    with app.app_context():
        admin = User.query.filter(or_(User.username=='admin', User.email=='admin@example.com')).first()
        if not admin:
            # ایجاد در صورت نبود
            admin = User(username='admin', email='admin@example.com', role='admin', is_active=True)
            db.session.add(admin)
            db.session.commit()
            print('ℹ️ کاربر admin وجود نداشت و ساخته شد.')
        # اطمینان از فعال بودن
        if not admin.is_active:
            admin.is_active = True
        admin.set_password(new_password)
        db.session.commit()
        print('✅ رمز عبور کاربر admin با موفقیت به‌روزرسانی شد.')
        # چاپ اطلاعات کمکی جهت عیب‌یابی
        print(f"username={admin.username}, email={admin.email}, active={admin.is_active}")
        print(f"hash_prefix={str(admin.password_hash)[:30]}")
        # تأیید صحت رمز جدید در همان کانکشن
        refreshed = User.query.filter_by(id=admin.id).first()
        ok = False
        if refreshed and isinstance(refreshed.password_hash, str):
            try:
                ok = check_password_hash(refreshed.password_hash, new_password)
            except Exception:
                ok = False
        print(f"verify_after_update={ok}")


if __name__ == '__main__':
    # مقدار پیش‌فرض
    reset_admin_password('admin123')


