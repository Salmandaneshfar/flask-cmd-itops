import os
from datetime import timedelta
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, 'instance', 'cms.db')

class Config:
    # تنظیمات پایه
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # تنظیمات دیتابیس
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{DEFAULT_SQLITE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300
    }
    
    # تنظیمات Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # تنظیمات امنیت
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'true').lower() in ['true', 'on', '1']
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('WTF_CSRF_TIME_LIMIT', 3600))
    
    # تنظیمات session
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 86400)))
    
    # تنظیمات آپلود فایل
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # تنظیمات ایمیل (اختیاری)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # تنظیمات پنل مدیریت
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    ITEMS_PER_PAGE = 10
    
    # تنظیمات لاگ
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # تنظیمات Caching (در حالت توسعه به صورت پیشفرض حافظه‌ای)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')  # 'simple' برای dev، 'redis' برای prod
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', REDIS_URL)
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))

    # تنظیمات Rate Limiter: در dev حافظه‌ای، در prod قابل override با REDIS
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    
    # تنظیمات FreeIPA
    FREEIPA_HOST = os.environ.get('FREEIPA_HOST', '192.168.0.36')
    FREEIPA_PORT = int(os.environ.get('FREEIPA_PORT', 389))
    FREEIPA_USE_SSL = os.environ.get('FREEIPA_USE_SSL', 'false').lower() in ['true', 'on', '1']
    FREEIPA_BASE_DN = os.environ.get('FREEIPA_BASE_DN', 'dc=mci,dc=local')
    FREEIPA_BIND_DN = os.environ.get('FREEIPA_BIND_DN', 'cn=mci,cn=users,dc=mci,dc=local')
    FREEIPA_BIND_PASSWORD = os.environ.get('FREEIPA_BIND_PASSWORD', '')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DEFAULT_SQLITE_PATH}"

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{DEFAULT_SQLITE_PATH}"

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
