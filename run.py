#!/usr/bin/env python3
"""
Flask CMS - سیستم مدیریت محتوا
"""

from app import create_app, db
from models import User, Server, Task, Content, Backup

def init_database():
    """ایجاد دیتابیس و کاربر پیش‌فرض"""
    app = create_app()
    
    with app.app_context():
        # ایجاد جداول
        db.create_all()
        
        # بررسی وجود کاربر admin
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ دیتابیس ایجاد شد و کاربر admin اضافه شد.")
            print("📧 نام کاربری: admin")
            print("🔑 رمز عبور: admin123")
        else:
            print("ℹ️ دیتابیس از قبل موجود است.")

def run_server():
    """اجرای سرور Flask"""
    app = create_app()
    
    print("🚀 شروع سرور Flask CMS...")
    print("🌐 آدرس: http://localhost:5000")
    print("👤 نام کاربری: admin")
    print("🔑 رمز عبور: admin123")
    print("⏹️ برای توقف سرور Ctrl+C را فشار دهید")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init_database()
    else:
        init_database()
        run_server()
