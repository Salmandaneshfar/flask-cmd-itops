from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin, user, editor
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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
    field_type = db.Column(db.String(50), nullable=False)  # text, number, email, date, select, textarea, checkbox
    model_name = db.Column(db.String(50), nullable=False)  # User, Server, Task, Content, Backup
    is_required = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    options = db.Column(db.Text)  # JSON string for select options
    placeholder = db.Column(db.String(200))
    help_text = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomField {self.name}>'
    
    def get_options(self):
        """تبدیل options از JSON string به list"""
        if self.options:
            try:
                import json
                return json.loads(self.options)
            except:
                return []
        return []
    
    def set_options(self, options_list):
        """تبدیل options از list به JSON string"""
        if options_list:
            import json
            self.options = json.dumps(options_list)
        else:
            self.options = None

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
