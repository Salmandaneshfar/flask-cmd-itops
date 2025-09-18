import os
import logging
import logging.handlers
from datetime import datetime
from flask import request, g
from config import Config

def setup_logging(app):
    """تنظیم سیستم logging پیشرفته"""
    
    # ایجاد دایرکتوری logs اگر وجود ندارد
    log_dir = os.path.dirname(Config.LOG_FILE)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            # در صورت عدم دسترسی، بعداً فقط به کنسول لاگ می‌کنیم
            pass
    
    # تنظیم سطح logging
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # تنظیم فرمت لاگ
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # تنظیم handler برای فایل (با fallback به کنسول در صورت خطا)
    file_handler = None
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
    except Exception:
        file_handler = None
    
    # تنظیم handler برای console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # تنظیم logger اصلی
    app.logger.setLevel(log_level)
    if file_handler:
        app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # تنظیم logger برای SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    
    # تنظیم logger برای Werkzeug
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # تنظیم logger برای Gunicorn
    logging.getLogger('gunicorn.error').setLevel(logging.INFO)
    logging.getLogger('gunicorn.access').setLevel(logging.INFO)
    
    # اضافه کردن context processor برای logging
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            app.logger.info(
                f"{request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s - "
                f"IP: {request.remote_addr} - "
                f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
            )
        return response
    
    # تنظیم error handlers برای logging
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Error: {request.path} - IP: {request.remote_addr}")
        return error
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Error: {request.path} - IP: {request.remote_addr} - Error: {str(error)}")
        return error
    
    app.logger.info("Logging system initialized successfully")

class SecurityLogger:
    """Logger مخصوص امنیت"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # تنظیم handler مخصوص امنیت (با fallback به کنسول)
        security_handler = None
        try:
            # اطمینان از وجود دایرکتوری
            os.makedirs('logs', exist_ok=True)
            security_handler = logging.handlers.RotatingFileHandler(
                'logs/security.log',
                maxBytes=5*1024*1024,  # 5MB
                backupCount=5,
                encoding='utf-8'
            )
            security_handler.setFormatter(logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(security_handler)
        except Exception:
            # اگر فایل قابل نوشتن نبود، روی کنسول لاگ می‌کنیم تا برنامه کرش نکند
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(console_handler)
    
    def log_login_attempt(self, username, ip, success=True):
        """ثبت تلاش ورود"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"LOGIN {status} - Username: {username} - IP: {ip}")
    
    def log_password_change(self, username, ip):
        """ثبت تغییر رمز عبور"""
        self.logger.info(f"PASSWORD_CHANGE - Username: {username} - IP: {ip}")
    
    def log_suspicious_activity(self, activity, ip, details=""):
        """ثبت فعالیت مشکوک"""
        self.logger.warning(f"SUSPICIOUS_ACTIVITY - {activity} - IP: {ip} - Details: {details}")
    
    def log_admin_action(self, admin_user, action, target, ip):
        """ثبت اقدامات ادمین"""
        self.logger.info(f"ADMIN_ACTION - User: {admin_user} - Action: {action} - Target: {target} - IP: {ip}")

# ایجاد instance از SecurityLogger
security_logger = SecurityLogger()

