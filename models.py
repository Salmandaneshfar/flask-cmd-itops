from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import base64
import binascii
import hashlib
import hmac

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin, user, editor
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        # استفاده اجباری از pbkdf2:sha256 برای سازگاری
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            # پشتیبانی از فرمت‌های قدیمی scrypt
            if isinstance(self.password_hash, str) and self.password_hash.startswith('scrypt:'):
                try:
                    # شکل مورد انتظار: scrypt:N:r:p$salt$hash
                    method_and_params, salt_str, hash_str = self.password_hash.split('$', 2)
                    _, n_str, r_str, p_str = method_and_params.split(':', 3)
                    n = int(n_str)
                    r = int(r_str)
                    p = int(p_str)

                    # دیکد کردن salt
                    salt_bytes = None
                    try:
                        salt_bytes = base64.b64decode(salt_str)
                    except binascii.Error:
                        try:
                            salt_bytes = bytes.fromhex(salt_str)
                        except ValueError:
                            salt_bytes = salt_str.encode('utf-8')

                    # دیکد کردن hash مقصد برای تعیین dklen و مقایسه
                    target_bytes = None
                    decode_ok = False
                    for decoder in (base64.b64decode, bytes.fromhex):
                        try:
                            target_bytes = decoder(hash_str)
                            decode_ok = True
                            break
                        except Exception:
                            continue
                    if not decode_ok:
                        # آخرین تلاش: استفاده خام
                        target_bytes = hash_str.encode('utf-8')

                    derived = hashlib.scrypt(
                        password.encode('utf-8'),
                        salt=salt_bytes,
                        n=n,
                        r=r,
                        p=p,
                        dklen=len(target_bytes) if len(target_bytes) > 0 else 64
                    )

                    if hmac.compare_digest(derived, target_bytes):
                        # ارتقا به الگوریتم پیش‌فرض امن فعلی (pbkdf2:sha256)
                        try:
                            self.set_password(password)
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                        return True
                    return False
                except Exception:
                    return False
            # سایر خطاها
            return False
    
    def __repr__(self):
        return f'<User {self.username}>'

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    os_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # فعال، غیرفعال، در حال بررسی
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Server {self.name}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(10), nullable=False, default='medium')  # low, medium, high, urgent
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')
    
    def __repr__(self):
        return f'<Task {self.title}>'

class SecurityProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200), nullable=False)
    contractor = db.Column(db.String(200), nullable=False)  # پیمانکار
    project_type = db.Column(db.String(50), nullable=False)  # network, os, application
    environment = db.Column(db.String(20), nullable=False)  # test, production
    security_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, in_progress, completed, failed, unknown
    priority = db.Column(db.String(10), nullable=False, default='medium')  # low, medium, high, critical
    description = db.Column(db.Text)
    security_requirements = db.Column(db.Text)  # الزامات امنیتی
    vulnerabilities_found = db.Column(db.Text)  # آسیب‌پذیری‌های یافت شده
    remediation_plan = db.Column(db.Text)  # برنامه اصلاح
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    estimated_duration = db.Column(db.Integer)  # مدت زمان تخمینی (روز)
    actual_duration = db.Column(db.Integer)  # مدت زمان واقعی (روز)
    
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_security_projects')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_security_projects')
    
    def __repr__(self):
        return f'<SecurityProject {self.project_name}>'

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # page, post, article
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft, published, archived
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    author = db.relationship('User', backref='contents')
    
    def __repr__(self):
        return f'<Content {self.title}>'

class Backup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    backup_type = db.Column(db.String(50), nullable=False)  # database, files, full
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Backup {self.name}>'

class CustomField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # text, number, email, date, textarea, checkbox, url, phone
    model_name = db.Column(db.String(50), nullable=False)  # User, Server, Task, Content, Backup
    is_required = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    placeholder = db.Column(db.String(200))
    help_text = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomField {self.name}>'
    

class CustomFieldValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('custom_field.id'), nullable=False)
    model_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)  # ID of the record in the target model
    value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    field = db.relationship('CustomField', backref='values')
    
    def __repr__(self):
        return f'<CustomFieldValue {self.field.name}: {self.value}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False, default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='notifications')
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # نام سرویس/اپلیکیشن
    service_type = db.Column(db.String(50), nullable=False)  # نوع سرویس (server, app, database, etc.)
    username = db.Column(db.String(200), nullable=False)
    password = db.Column(db.Text, nullable=False)  # رمز عبور رمزنگاری شده
    url = db.Column(db.String(500))  # آدرس سرویس
    description = db.Column(db.Text)  # توضیحات
    tags = db.Column(db.String(500))  # برچسب‌ها (comma separated)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = db.Column(db.DateTime)  # آخرین استفاده
    
    user = db.relationship('User', backref='credentials')
    
    def set_password(self, password):
        """رمزنگاری پسورد"""
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """بررسی پسورد"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)
    
    def get_tags_list(self):
        """دریافت لیست برچسب‌ها"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags_list(self, tags_list):
        """تنظیم لیست برچسب‌ها"""
        self.tags = ', '.join(tags_list) if tags_list else None
    
    def __repr__(self):
        return f'<Credential {self.name}>'


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # نام سرویس/نشانه
    address = db.Column(db.String(500), nullable=False)  # آدرس یا دامنه یا IP
    port = db.Column(db.Integer)  # پورت سرویس (اختیاری)
    url = db.Column(db.String(500))  # اگر لینک کامل دارید
    description = db.Column(db.Text)  # توضیحات
    is_favorite = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='bookmarks')

    def computed_url(self):
        """ساخت URL در صورت ارائه address و port، اگر url خالی بود"""
        if self.url:
            return self.url
        if self.address and self.port:
            return f"http://{self.address}:{self.port}"
        if self.address:
            return f"http://{self.address}"
        return None

    def __repr__(self):
        return f'<Bookmark {self.name}>'


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    content_type = db.Column(db.String(120))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship('User', backref='attachments')

    def __repr__(self):
        return f'<Attachment {self.file_name} for {self.model_name}#{self.record_id}>'


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # internal, external
    category = db.Column(db.String(20), nullable=False, default='internal')
    username = db.Column(db.String(120), nullable=False)
    dongle_name = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    department = db.Column(db.String(120))
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by], backref='people_created')

    def __repr__(self):
        return f'<Person {self.username} ({self.category})>'

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(80))
    action = db.Column(db.String(100), nullable=False)  # e.g., login, add_task, edit_task
    model_name = db.Column(db.String(50))  # Task, Server, User, Credential, etc.
    record_id = db.Column(db.Integer)
    method = db.Column(db.String(10))  # GET, POST, ...
    path = db.Column(db.String(255))
    status_code = db.Column(db.Integer)
    ip_address = db.Column(db.String(100))
    user_agent = db.Column(db.String(255))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action} by {self.username or self.user_id}>'


class LookupItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.String(50), nullable=False)  # e.g., department, office, vendor
    key = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('group', 'key', name='uq_lookup_group_key'),
    )

    def __repr__(self):
        return f'<LookupItem {self.group}:{self.key}>'


