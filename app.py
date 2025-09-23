from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import os
import sqlite3
import redis

from config import config
from sqlalchemy import or_, text
from models import db, User, Server, Task, Content, Backup, CustomField, CustomFieldValue, SecurityProject, Notification, Credential, Bookmark, Attachment, ActivityLog, Person, LookupItem, FreeIPAServer, FreeIPAUser, FreeIPAGroup, FreeIPAUserGroup, UserPassword, SMSTemplate, SMSLog
from app_custom_fields import custom_fields_bp
from freeipa_service import freeipa_service
from freeipa_routes import freeipa_bp
from forms import (LoginForm, UserForm, EditUserForm, ChangePasswordForm, 
                  ServerForm, TaskForm, ContentForm, BackupForm,
                  CustomFieldForm, CustomFieldEditForm, SecurityProjectForm, SecurityProjectEditForm,
                  CredentialForm, CredentialEditForm, CredentialSearchForm, BookmarkForm, BookmarkEditForm,
                  PersonForm, PersonEditForm)
from logging_config import setup_logging, security_logger

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Disable template caching in development
    if config_name == 'development':
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize CSRF Protection
    csrf = CSRFProtect(app)
    
    # Initialize Cache
    cache = Cache(app)
    
    # Initialize Rate Limiter with Redis storage
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URI')
    )
    limiter.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'لطفاً ابتدا وارد شوید.'
    login_manager.login_message_category = 'info'
    
    # Ensure database tables exist (simple bootstrap; replace with migrations in production)
    try:
        with app.app_context():
            db.create_all()
    except Exception:
        pass

    # Setup logging
    setup_logging(app)
    
    # Register custom fields blueprint
    app.register_blueprint(custom_fields_bp)
    app.register_blueprint(freeipa_bp)
    # Exempt FreeIPA blueprint from CSRF to allow simple HTML forms without Flask-WTF
    try:
        csrf.exempt(freeipa_bp)
    except Exception:
        pass
    
    # Test route to check template changes
    @app.route('/test-template')
    def test_template():
        return render_template('base.html')
    
    # Final dropdown test route
    @app.route('/test-dropdown-final')
    def test_dropdown_final():
        return render_template('test_dropdown_final.html')
    
    
    # Comprehensive test route for all fields
    @app.route('/test-all-fields')
    def test_all_fields():
        return render_template('test_all_fields.html')

    # Ensure ActivityLog table has required columns (handles existing DBs without migrations)
    try:
        with app.app_context():
            engine = db.get_engine()
            conn = engine.connect()
            try:
                # Detect existing columns (SQLite and Postgres compatible)
                inspector = db.inspect(engine)
                columns = {col['name'] for col in inspector.get_columns('activity_log')}
                # Columns we expect to exist
                required_columns = {
                    'id','user_id','username','action','model_name','record_id',
                    'method','path','status_code','ip_address','user_agent','details','created_at'
                }
                missing = required_columns - columns
                # Add missing columns where possible (SQLite supports simple ADD COLUMN)
                for col in missing:
                    if col == 'username':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN username VARCHAR(80)"))
                    elif col == 'method':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN method VARCHAR(10)"))
                    elif col == 'path':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN path VARCHAR(255)"))
                    elif col == 'status_code':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN status_code INTEGER"))
                    elif col == 'ip_address':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN ip_address VARCHAR(100)"))
                    elif col == 'user_agent':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN user_agent VARCHAR(255)"))
                    elif col == 'details':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN details TEXT"))
                    elif col == 'model_name':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN model_name VARCHAR(50)"))
                    elif col == 'record_id':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN record_id INTEGER"))
                    elif col == 'created_at':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN created_at DATETIME"))
                    elif col == 'user_id':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN user_id INTEGER"))
                    elif col == 'action':
                        conn.execute(text("ALTER TABLE activity_log ADD COLUMN action VARCHAR(100)"))
                    elif col == 'id':
                        # Primary key missing implies table doesn't exist as expected; skip here
                        pass
            finally:
                conn.close()
    except Exception:
        # Silent: do not block app startup if ALTER not supported
        pass
    
    # Activity logging helper
    def log_activity(action, model_name=None, record_id=None, status_code=None, details=None):
        try:
            log_entry = ActivityLog(
                user_id=current_user.id if current_user.is_authenticated else None,
                username=current_user.username if current_user.is_authenticated else 'Anonymous',
                action=action,
                model_name=model_name,
                record_id=record_id,
                method=request.method,
                path=request.path,
                status_code=status_code,
                details=details,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Don't fail the main request if logging fails
            pass
    
    # Make log_activity available globally
    app.log_activity = log_activity
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Global activity logger for all write requests (fallback)
    @app.after_request
    def log_write_requests(response):
        try:
            # Skip static and health endpoints
            if request.endpoint in ['static', 'health_check']:
                return response
            # Log only state-changing methods; GETs are noisy
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                app.log_activity(
                    action=f"{request.method.lower()}",
                    model_name=request.endpoint,
                    record_id=None,
                    status_code=response.status_code,
                    details=None
                )
        except Exception:
            pass
        return response
    
    # Ensure required directories exist
    os.makedirs('instance', exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancer"""
        try:
            # Check database connection
            db.session.execute(text('SELECT 1'))
            db_status = 'healthy'
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'
        
        try:
            # Check Redis connection
            redis_client = redis.from_url(app.config['REDIS_URL'])
            redis_client.ping()
            redis_status = 'healthy'
        except Exception as e:
            redis_status = f'unhealthy: {str(e)}'
        
        return jsonify({
            'status': 'healthy' if db_status == 'healthy' and redis_status == 'healthy' else 'unhealthy',
            'database': db_status,
            'redis': redis_status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200 if db_status == 'healthy' and redis_status == 'healthy' else 503
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("10 per minute")
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data) and user.is_active:
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log successful login
                security_logger.log_login_attempt(
                    username=form.username.data,
                    ip=request.remote_addr,
                    success=True
                )
                app.log_activity('login', 'user', user.id, 200, f'Successful login for {form.username.data}')
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                # Log failed login attempt
                security_logger.log_login_attempt(
                    username=form.username.data,
                    ip=request.remote_addr,
                    success=False
                )
                flash('نام کاربری یا رمز عبور اشتباه است.', 'error')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        user_id = current_user.id
        username = current_user.username
        logout_user()
        app.log_activity('logout', 'user', user_id, 200, f'User {username} logged out')
        return redirect(url_for('login'))
    
    # Main routes
    @app.route('/')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get statistics
        stats = {
            'users_count': User.query.count(),
            'servers_count': Server.query.count(),
            'tasks_count': Task.query.count(),
            'content_count': Content.query.count(),
            'active_tasks': Task.query.filter_by(status='in_progress').count(),
            'published_content': Content.query.filter_by(status='published').count()
        }
        
        # Recent activities
        recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
        recent_content = Content.query.order_by(Content.created_at.desc()).limit(5).all()
        
        return render_template('dashboard.html', stats=stats, recent_tasks=recent_tasks, recent_content=recent_content)
    
    # User management routes
    @app.route('/users')
    @login_required
    def users():
        page = request.args.get('page', 1, type=int)
        query = request.args.get('query', '')
        role = request.args.get('role', '')
        status = request.args.get('status', '')
        
        # ساخت کوئری پایه
        users_query = User.query
        
        # اعمال فیلترها
        if query:
            users_query = users_query.filter(
                User.username.contains(query) | 
                User.email.contains(query)
            )
        
        if role:
            users_query = users_query.filter_by(role=role)
        
        if status:
            if status == 'active':
                users_query = users_query.filter_by(is_active=True)
            elif status == 'inactive':
                users_query = users_query.filter_by(is_active=False)
        
        users = users_query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        
        # دریافت فیلدهای سفارشی برای کاربران
        custom_fields_data = get_custom_fields_for_records(users.items, 'User')
        custom_fields_structure = get_custom_fields_structure(custom_fields_data)
        
        return render_template('users.html', users=users, custom_fields_data=custom_fields_data, custom_fields_structure=custom_fields_structure)
    
    @app.route('/users/add', methods=['GET', 'POST'])
    @login_required
    def add_user():
        if current_user.role != 'admin':
            flash('شما دسترسی لازم را ندارید.', 'error')
            return redirect(url_for('users'))
        
        form = UserForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data,
                is_active=form.is_active.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # برای گرفتن ID
            
            # پردازش فیلدهای سفارشی
            for key, value in request.form.items():
                if key.startswith('custom_field_'):
                    field_id = key.replace('custom_field_', '')
                    try:
                        field_value = CustomFieldValue(
                            field_id=int(field_id),
                            model_name='User',
                            record_id=user.id,
                            value=value
                        )
                        db.session.add(field_value)
                    except ValueError:
                        continue
            
            db.session.commit()
            app.log_activity('create', 'user', user.id, 200, f'Created user: {user.username}')
            flash('کاربر با موفقیت اضافه شد.', 'success')
            return redirect(url_for('users'))
        
        return render_template('add_user.html', form=form)
    
    @app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_user(id):
        if current_user.role != 'admin':
            flash('شما دسترسی لازم را ندارید.', 'error')
            return redirect(url_for('users'))
        
        user = User.query.get_or_404(id)
        form = EditUserForm(obj=user)
        
        if form.validate_on_submit():
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data
            user.is_active = form.is_active.data
            
            # پردازش فیلدهای سفارشی
            for key, value in request.form.items():
                if key.startswith('custom_field_'):
                    field_id = key.replace('custom_field_', '')
                    try:
                        # پیدا کردن یا ایجاد مقدار فیلد
                        field_value = CustomFieldValue.query.filter_by(
                            field_id=int(field_id),
                            model_name='User',
                            record_id=user.id
                        ).first()
                        
                        if field_value:
                            field_value.value = value
                        else:
                            field_value = CustomFieldValue(
                                field_id=int(field_id),
                                model_name='User',
                                record_id=user.id,
                                value=value
                            )
                            db.session.add(field_value)
                    except ValueError:
                        continue
            
            db.session.commit()
            flash('کاربر با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('users'))
        
        return render_template('edit_user.html', form=form, user=user)
    
    @app.route('/users/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_user(id):
        if current_user.role != 'admin':
            flash('شما دسترسی لازم را ندارید.', 'error')
            return redirect(url_for('users'))
        
        user = User.query.get_or_404(id)
        
        # جلوگیری از حذف خود کاربر
        if user.id == current_user.id:
            flash('نمی‌توانید خودتان را حذف کنید.', 'error')
            return redirect(url_for('users'))
        
        db.session.delete(user)
        db.session.commit()
        flash('کاربر با موفقیت حذف شد.', 'success')
        return redirect(url_for('users'))
    
    # Server management routes
    @app.route('/servers')
    @login_required
    def servers():
        page = request.args.get('page', 1, type=int)
        query = request.args.get('query', '')
        os_type = request.args.get('os_type', '')
        status = request.args.get('status', '')
        
        # ساخت کوئری پایه
        servers_query = Server.query
        
        # اعمال فیلترها
        if query:
            servers_query = servers_query.filter(
                Server.name.contains(query) | 
                Server.description.contains(query)
            )
        
        if os_type:
            servers_query = servers_query.filter_by(os_type=os_type)
        
        if status:
            servers_query = servers_query.filter_by(status=status)
        
        servers = servers_query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        
        # دریافت فیلدهای سفارشی برای سرورها
        custom_fields_data = get_custom_fields_for_records(servers.items, 'Server')
        custom_fields_structure = get_custom_fields_structure(custom_fields_data)
        
        return render_template('servers.html', servers=servers, custom_fields_data=custom_fields_data, custom_fields_structure=custom_fields_structure)
    
    @app.route('/servers/add', methods=['GET', 'POST'])
    @login_required
    def add_server():
        form = ServerForm()
        if form.validate_on_submit():
            server = Server(
                name=form.name.data,
                ip_address=form.ip_address.data,
                os_type=form.os_type.data,
                status=form.status.data,
                description=form.description.data
            )
            db.session.add(server)
            db.session.flush()  # برای گرفتن ID
            
            # پردازش فیلدهای سفارشی
            for key, value in request.form.items():
                if key.startswith('custom_field_'):
                    field_id = key.replace('custom_field_', '')
                    try:
                        field_value = CustomFieldValue(
                            field_id=int(field_id),
                            model_name='Server',
                            record_id=server.id,
                            value=value
                        )
                        db.session.add(field_value)
                    except ValueError:
                        continue
            
            db.session.commit()
            flash('سرور با موفقیت اضافه شد.', 'success')
            return redirect(url_for('servers'))
        
        return render_template('add_server.html', form=form)
    
    @app.route('/servers/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_server(id):
        server = Server.query.get_or_404(id)
        form = ServerForm(obj=server)
        
        if form.validate_on_submit():
            server.name = form.name.data
            server.ip_address = form.ip_address.data
            server.os_type = form.os_type.data
            server.status = form.status.data
            server.description = form.description.data
            server.updated_at = datetime.utcnow()
            
            # پردازش فیلدهای سفارشی
            for key, value in request.form.items():
                if key.startswith('custom_field_'):
                    field_id = key.replace('custom_field_', '')
                    try:
                        # پیدا کردن یا ایجاد مقدار فیلد
                        field_value = CustomFieldValue.query.filter_by(
                            field_id=int(field_id),
                            model_name='Server',
                            record_id=server.id
                        ).first()
                        
                        if field_value:
                            field_value.value = value
                        else:
                            field_value = CustomFieldValue(
                                field_id=int(field_id),
                                model_name='Server',
                                record_id=server.id,
                                value=value
                            )
                            db.session.add(field_value)
                    except ValueError:
                        continue
            
            db.session.commit()
            flash('سرور با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('servers'))
        
        return render_template('edit_server.html', form=form, server=server)
    
    @app.route('/servers/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_server(id):
        server = Server.query.get_or_404(id)
        db.session.delete(server)
        db.session.commit()
        flash('سرور با موفقیت حذف شد.', 'success')
        return redirect(url_for('servers'))
    
    # Task management routes
    @app.route('/tasks')
    @login_required
    def tasks():
        page = request.args.get('page', 1, type=int)
        query = request.args.get('query', '')
        priority = request.args.get('priority', '')
        status = request.args.get('status', '')
        assigned_to = request.args.get('assigned_to', '')
        
        # ساخت کوئری پایه
        tasks_query = Task.query
        
        # اعمال فیلترها
        if query:
            tasks_query = tasks_query.filter(
                Task.title.contains(query) | 
                Task.description.contains(query)
            )
        
        if priority:
            tasks_query = tasks_query.filter_by(priority=priority)
        
        if status:
            tasks_query = tasks_query.filter_by(status=status)
        
        if assigned_to:
            tasks_query = tasks_query.filter_by(assigned_to=assigned_to)
        
        tasks = tasks_query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        
        # دریافت فیلدهای سفارشی برای تسک‌ها
        custom_fields_data = get_custom_fields_for_records(tasks.items, 'Task')
        custom_fields_structure = get_custom_fields_structure(custom_fields_data)
        
        return render_template('tasks.html', tasks=tasks, User=User, custom_fields_data=custom_fields_data, custom_fields_structure=custom_fields_structure)
    
    @app.route('/tasks/add', methods=['GET', 'POST'])
    @login_required
    def add_task():
        form = TaskForm()
        form.assigned_to.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]
        
        if form.validate_on_submit():
            task = Task(
                title=form.title.data,
                description=form.description.data,
                priority=form.priority.data,
                assigned_to=form.assigned_to.data,
                created_by=current_user.id,
                due_date=form.due_date.data
            )
            db.session.add(task)
            db.session.flush()  # برای گرفتن ID
            
            # پردازش فیلدهای سفارشی
            for key, value in request.form.items():
                if key.startswith('custom_field_'):
                    field_id = key.replace('custom_field_', '')
                    try:
                        field_value = CustomFieldValue(
                            field_id=int(field_id),
                            model_name='Task',
                            record_id=task.id,
                            value=value
                        )
                        db.session.add(field_value)
                    except ValueError:
                        continue
            
            db.session.commit()
            flash('تسک با موفقیت اضافه شد.', 'success')
            return redirect(url_for('tasks'))
        
        return render_template('add_task.html', form=form)
    
    @app.route('/tasks/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_task(id):
        task = Task.query.get_or_404(id)
        form = TaskForm(obj=task)
        form.assigned_to.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]
        
        if form.validate_on_submit():
            task.title = form.title.data
            task.description = form.description.data
            task.priority = form.priority.data
            task.assigned_to = form.assigned_to.data
            task.due_date = form.due_date.data
            task.updated_at = datetime.utcnow()
            
            # پردازش فیلدهای سفارشی
            for key, value in request.form.items():
                if key.startswith('custom_field_'):
                    field_id = key.replace('custom_field_', '')
                    try:
                        # پیدا کردن یا ایجاد مقدار فیلد
                        field_value = CustomFieldValue.query.filter_by(
                            field_id=int(field_id),
                            model_name='Task',
                            record_id=task.id
                        ).first()
                        
                        if field_value:
                            field_value.value = value
                        else:
                            field_value = CustomFieldValue(
                                field_id=int(field_id),
                                model_name='Task',
                                record_id=task.id,
                                value=value
                            )
                            db.session.add(field_value)
                    except ValueError:
                        continue
            
            db.session.commit()
            flash('تسک با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('tasks'))
        
        return render_template('edit_task.html', form=form, task=task)
    
    @app.route('/tasks/delete/<int:id>', methods=['POST'])
    @login_required
    @csrf.exempt
    def delete_task(id):
        task = Task.query.get_or_404(id)
        db.session.delete(task)
        db.session.commit()
        flash('تسک با موفقیت حذف شد.', 'success')
        return redirect(url_for('tasks'))
    
    # Security Projects management routes
    @app.route('/security-projects')
    @login_required
    def security_projects():
        page = request.args.get('page', 1, type=int)
        query = request.args.get('query', '')
        project_type = request.args.get('project_type', '')
        environment = request.args.get('environment', '')
        security_status = request.args.get('security_status', '')
        
        # ساخت کوئری پایه
        projects_query = SecurityProject.query
        
        # اعمال فیلترها
        if query:
            projects_query = projects_query.filter(
                SecurityProject.project_name.contains(query) | 
                SecurityProject.description.contains(query)
            )
        
        if project_type:
            projects_query = projects_query.filter_by(project_type=project_type)
        
        if environment:
            projects_query = projects_query.filter_by(environment=environment)
        
        if security_status:
            projects_query = projects_query.filter_by(security_status=security_status)
        
        projects = projects_query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('security_projects.html', projects=projects)
    
    @app.route('/security-projects/add', methods=['GET', 'POST'])
    @login_required
    def add_security_project():
        form = SecurityProjectForm()
        form.assigned_to.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]
        
        if form.validate_on_submit():
            project = SecurityProject(
                project_name=form.project_name.data,
                contractor=form.contractor.data,
                project_type=form.project_type.data,
                environment=form.environment.data,
                security_status=form.security_status.data,
                priority=form.priority.data,
                description=form.description.data,
                security_requirements=form.security_requirements.data,
                vulnerabilities_found=form.vulnerabilities_found.data,
                remediation_plan=form.remediation_plan.data,
                assigned_to=form.assigned_to.data,
                created_by=current_user.id,
                start_date=form.start_date.data,
                estimated_duration=int(form.estimated_duration.data) if form.estimated_duration.data else None
            )
            db.session.add(project)
            db.session.commit()
            flash('پروژه امنیتی با موفقیت اضافه شد.', 'success')
            return redirect(url_for('security_projects'))
        
        return render_template('add_security_project.html', form=form)
    
    @app.route('/security-projects/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_security_project(id):
        project = SecurityProject.query.get_or_404(id)
        form = SecurityProjectEditForm(obj=project)
        form.assigned_to.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]
        
        if form.validate_on_submit():
            project.project_name = form.project_name.data
            project.contractor = form.contractor.data
            project.project_type = form.project_type.data
            project.environment = form.environment.data
            project.security_status = form.security_status.data
            project.priority = form.priority.data
            project.description = form.description.data
            project.security_requirements = form.security_requirements.data
            project.vulnerabilities_found = form.vulnerabilities_found.data
            project.remediation_plan = form.remediation_plan.data
            project.assigned_to = form.assigned_to.data
            project.start_date = form.start_date.data
            project.completion_date = form.completion_date.data
            project.estimated_duration = int(form.estimated_duration.data) if form.estimated_duration.data else None
            project.actual_duration = int(form.actual_duration.data) if form.actual_duration.data else None
            
            # محاسبه مدت زمان واقعی
            if project.start_date and project.completion_date:
                delta = project.completion_date - project.start_date
                project.actual_duration = delta.days
            
            project.updated_at = datetime.utcnow()
            db.session.commit()
            flash('پروژه امنیتی با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('security_projects'))
        
        return render_template('edit_security_project.html', form=form, project=project)
    
    @app.route('/security-projects/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_security_project(id):
        project = SecurityProject.query.get_or_404(id)
        db.session.delete(project)
        db.session.commit()
        flash('پروژه امنیتی با موفقیت حذف شد.', 'success')
        return redirect(url_for('security_projects'))
    
    # Content management routes (keeping for backward compatibility)
    @app.route('/content')
    @login_required
    def content():
        page = request.args.get('page', 1, type=int)
        query = request.args.get('query', '')
        content_type = request.args.get('content_type', '')
        status = request.args.get('status', '')
        
        # ساخت کوئری پایه
        content_query = Content.query
        
        # اعمال فیلترها
        if query:
            content_query = content_query.filter(
                Content.title.contains(query) | 
                Content.content.contains(query)
            )
        
        if content_type:
            content_query = content_query.filter_by(content_type=content_type)
        
        if status:
            content_query = content_query.filter_by(status=status)
        
        content = content_query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('content.html', content=content)
    
    @app.route('/content/add', methods=['GET', 'POST'])
    @login_required
    def add_content():
        form = ContentForm()
        if form.validate_on_submit():
            content = Content(
                title=form.title.data,
                content=form.content.data,
                slug=form.slug.data,
                content_type=form.content_type.data,
                status=form.status.data,
                author_id=current_user.id
            )
            if form.status.data == 'published':
                content.published_at = datetime.utcnow()
            
            db.session.add(content)
            db.session.commit()
            flash('محتوا با موفقیت اضافه شد.', 'success')
            return redirect(url_for('content'))
        
        return render_template('add_content.html', form=form)
    
    @app.route('/content/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_content(id):
        content = Content.query.get_or_404(id)
        form = ContentForm(obj=content)
        
        if form.validate_on_submit():
            content.title = form.title.data
            content.content = form.content.data
            content.slug = form.slug.data
            content.content_type = form.content_type.data
            content.status = form.status.data
            
            if form.status.data == 'published' and content.status != 'published':
                content.published_at = datetime.utcnow()
            
            db.session.commit()
            flash('محتوا با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('content'))
        
        return render_template('edit_content.html', form=form, content=content)
    
    @app.route('/content/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_content(id):
        content = Content.query.get_or_404(id)
        
        # بررسی دسترسی - فقط نویسنده یا ادمین می‌تواند حذف کند
        if content.author_id != current_user.id and current_user.role != 'admin':
            flash('شما دسترسی لازم را ندارید.', 'error')
            return redirect(url_for('content'))
        
        db.session.delete(content)
        db.session.commit()
        flash('محتوا با موفقیت حذف شد.', 'success')
        return redirect(url_for('content'))
    
    # Backup management routes
    @app.route('/backups')
    @login_required
    def backups():
        page = request.args.get('page', 1, type=int)
        query = request.args.get('query', '')
        backup_type = request.args.get('backup_type', '')
        status = request.args.get('status', '')
        
        # ساخت کوئری پایه
        backups_query = Backup.query
        
        # اعمال فیلترها
        if query:
            backups_query = backups_query.filter(
                Backup.name.contains(query) | 
                Backup.file_path.contains(query)
            )
        
        if backup_type:
            backups_query = backups_query.filter_by(backup_type=backup_type)
        
        if status:
            backups_query = backups_query.filter_by(status=status)
        
        backups = backups_query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('backups.html', backups=backups)
    
    @app.route('/backups/add', methods=['GET', 'POST'])
    @login_required
    def add_backup():
        form = BackupForm()
        if form.validate_on_submit():
            backup = Backup(
                name=form.name.data,
                file_path=form.file_path.data,
                file_size=form.file_size.data,
                backup_type=form.backup_type.data,
                status=form.status.data
            )
            db.session.add(backup)
            db.session.commit()
            flash('بکاپ با موفقیت اضافه شد.', 'success')
            return redirect(url_for('backups'))
        
        return render_template('add_backup.html', form=form)
    
    @app.route('/backups/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_backup(id):
        backup = Backup.query.get_or_404(id)
        form = BackupForm(obj=backup)
        
        if form.validate_on_submit():
            backup.name = form.name.data
            backup.file_path = form.file_path.data
            backup.file_size = form.file_size.data
            backup.backup_type = form.backup_type.data
            backup.status = form.status.data
            if form.status.data == 'completed':
                backup.completed_at = datetime.utcnow()
            db.session.commit()
            flash('بکاپ با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('backups'))
        
        return render_template('edit_backup.html', form=form, backup=backup)
    
    @app.route('/backups/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_backup(id):
        backup = Backup.query.get_or_404(id)
        db.session.delete(backup)
        db.session.commit()
        flash('بکاپ با موفقیت حذف شد.', 'success')
        return redirect(url_for('backups'))
    
    # Search functionality
    @app.route('/search', methods=['GET', 'POST'])
    @login_required
    def search():
        form = SearchForm()
        results = []
        
        if form.validate_on_submit():
            query = form.query.data
            search_type = form.search_type.data
            
            if search_type == 'all' or search_type == 'users':
                users = User.query.filter(User.username.contains(query) | User.email.contains(query)).all()
                results.extend([('user', u) for u in users])
            
            if search_type == 'all' or search_type == 'servers':
                servers = Server.query.filter(Server.name.contains(query) | Server.description.contains(query)).all()
                results.extend([('server', s) for s in servers])
            
            if search_type == 'all' or search_type == 'tasks':
                tasks = Task.query.filter(Task.title.contains(query) | Task.description.contains(query)).all()
                results.extend([('task', t) for t in tasks])
            
            if search_type == 'all' or search_type == 'content':
                content = Content.query.filter(Content.title.contains(query) | Content.content.contains(query)).all()
                results.extend([('content', c) for c in content])
        
        return render_template('search.html', form=form, results=results)
    
    # Custom Fields Management - Redirect to new system
    @app.route('/custom-fields')
    @login_required
    def custom_fields():
        return redirect(url_for('custom_fields.list_fields'))
    
    @app.route('/custom-fields/add', methods=['GET', 'POST'])
    @login_required
    def add_custom_field():
        return redirect(url_for('custom_fields.add_field'))
    
    @app.route('/custom-fields/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_custom_field(id):
        return redirect(url_for('custom_fields.edit_field', id=id))
    
    @app.route('/custom-fields/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_custom_field(id):
        return redirect(url_for('custom_fields.delete_field', id=id))
    
    # API for dynamic field values - Redirect to new system
    @app.route('/api/custom-field-value', methods=['POST'])
    @login_required
    def save_custom_field_value():
        return redirect(url_for('custom_fields.save_field_value'))
    
    @app.route('/api/custom-field-values/<model_name>/<int:record_id>')
    @login_required
    def get_custom_field_values(model_name, record_id):
        return redirect(url_for('custom_fields.get_field_values', model_name=model_name, record_id=record_id))
    
    # API برای دریافت فیلدهای داینامیک یک مدل
    @app.route('/api/custom-fields/<model_name>')
    @login_required
    def get_custom_fields_for_model(model_name):
        return redirect(url_for('custom_fields.get_fields_for_model', model_name=model_name))
    
    # API برای حذف فیلد سفارشی
    @app.route('/api/custom-fields/<int:field_id>/delete', methods=['POST'])
    @login_required
    def delete_custom_field_api(field_id):
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'دسترسی غیرمجاز'})
        
        field = CustomField.query.get_or_404(field_id)
        
        # حذف مقادیر مربوطه
        CustomFieldValue.query.filter_by(field_id=field_id).delete()
        
        db.session.delete(field)
        db.session.commit()
        
        return jsonify({'success': True})
    
    # API برای تغییر وضعیت فیلد
    @app.route('/api/custom-fields/<int:field_id>/toggle', methods=['POST'])
    @login_required
    def toggle_custom_field(field_id):
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'دسترسی غیرمجاز'})
        
        field = CustomField.query.get_or_404(field_id)
        field.is_active = not field.is_active
        db.session.commit()
        
        return jsonify({'success': True, 'is_active': field.is_active})
    
    # API routes for AJAX
    @app.route('/api/task/<int:id>/status', methods=['POST'])
    @login_required
    @csrf.exempt
    def update_task_status(id):
        task = Task.query.get_or_404(id)
        new_status = request.json.get('status')
        
        if new_status in ['pending', 'in_progress', 'completed', 'cancelled']:
            task.status = new_status
            if new_status == 'completed':
                task.completed_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'status': new_status})
        
        return jsonify({'success': False, 'error': 'Invalid status'})
    
    # Notification API
    @app.route('/api/notifications')
    @login_required
    def get_notifications():
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
        return jsonify([{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications])
    
    @app.route('/api/notifications/<int:id>/read', methods=['POST'])
    @login_required
    def mark_notification_read(id):
        notification = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        notification.mark_as_read()
        return jsonify({'success': True})
    
    @app.route('/api/notifications/read-all', methods=['POST'])
    @login_required
    def mark_all_notifications_read():
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True, 'read_at': datetime.utcnow()})
        db.session.commit()
        return jsonify({'success': True})

    # Admin: Activity Logs page
    @app.route('/admin/activity-logs')
    @login_required
    def activity_logs():
        if current_user.role != 'admin':
            flash('دسترسی غیرمجاز.', 'error')
            return redirect(url_for('dashboard'))

        page = request.args.get('page', 1, type=int)
        query = request.args.get('query', '')
        action = request.args.get('action', '')
        username = request.args.get('username', '')
        model_name = request.args.get('model_name', '')

        logs_q = ActivityLog.query.order_by(ActivityLog.created_at.desc())
        if query:
            like = f"%{query}%"
            logs_q = logs_q.filter(or_(ActivityLog.details.ilike(like), ActivityLog.path.ilike(like)))
        if action:
            logs_q = logs_q.filter_by(action=action)
        if username:
            logs_q = logs_q.filter(ActivityLog.username.ilike(f"%{username}%"))
        if model_name:
            logs_q = logs_q.filter_by(model_name=model_name)

        logs = logs_q.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('activity_logs.html', logs=logs)

    # API: recent activity logs for dashboard live refresh
    @app.route('/api/activity-logs/recent')
    @login_required
    def api_activity_logs_recent():
        limit = request.args.get('limit', 5, type=int)
        # Dashboard widget is admin-only; return global recent logs
        items = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
        def to_iso_z(dt):
            try:
                # Always mark as UTC (server stores naive UTC)
                return (dt.isoformat() + ('Z' if dt.tzinfo is None else ''))
            except Exception:
                return None
        resp = jsonify({
            'success': True,
            'items': [
                {
                    'id': i.id,
                    'username': i.username,
                    'user_id': i.user_id,
                    'action': i.action,
                    'model_name': i.model_name,
                    'record_id': i.record_id,
                    'method': i.method,
                    'path': i.path,
                    'status_code': i.status_code,
                    'created_at': to_iso_z(i.created_at),
                    'created_at_ts': int(i.created_at.timestamp() * 1000) if i.created_at else None
                }
                for i in items
            ]
        })
        # Prevent any intermediary/browser caching
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        return resp

    # Bookmarks
    @app.route('/bookmarks')
    @login_required
    def bookmarks():
        page = request.args.get('page', 1, type=int)
        query = request.args.get('query', '')
        only_fav = request.args.get('fav', '') == '1'

        bookmarks_query = Bookmark.query.filter_by(created_by=current_user.id)
        if query:
            bookmarks_query = bookmarks_query.filter(
                Bookmark.name.contains(query) | Bookmark.address.contains(query) | Bookmark.description.contains(query)
            )
        if only_fav:
            bookmarks_query = bookmarks_query.filter_by(is_favorite=True)

        bookmarks_page = bookmarks_query.order_by(Bookmark.is_favorite.desc(), Bookmark.updated_at.desc()).paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('bookmarks.html', bookmarks=bookmarks_page, query=query, only_fav=only_fav)

    # People (internal/external users of systems)
    
    # Lookup Items (dropdown lists) - integrated with custom fields
    @app.route('/lookups')
    @login_required
    def lookups():
        if current_user.role != 'admin':
            flash('دسترسی غیرمجاز.', 'error')
            return redirect(url_for('dashboard'))
        group = request.args.get('group', 'department')
        items = LookupItem.query.filter_by(group=group).order_by(LookupItem.order.asc(), LookupItem.label.asc()).all()
        return render_template('lookups.html', group=group, items=items)

    @app.route('/lookups/add', methods=['GET', 'POST'])
    @login_required
    def add_lookup():
        if current_user.role != 'admin':
            flash('دسترسی غیرمجاز.', 'error')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            group = request.form.get('group') or 'department'
            key = request.form.get('key') or request.form.get('label')
            label = request.form.get('label')
            order = int(request.form.get('order') or 0)
            if not label:
                flash('برچسب الزامی است', 'error')
                return redirect(url_for('lookups', group=group))
            item = LookupItem(group=group, key=key, label=label, order=order, is_active=True)
            db.session.add(item)
            db.session.commit()
            app.log_activity('create', 'LookupItem', item.id, 200, f'Add {group}:{label}')
            flash('آیتم با موفقیت اضافه شد.', 'success')
            return redirect(url_for('lookups', group=group))
        return render_template('add_lookup.html')

    @app.route('/lookups/<int:id>/toggle', methods=['POST'])
    @login_required
    def toggle_lookup(id):
        if current_user.role != 'admin':
            return jsonify({'success': False})
        item = LookupItem.query.get_or_404(id)
        item.is_active = not item.is_active
        db.session.commit()
        app.log_activity('update', 'LookupItem', item.id, 200, f'Toggle {item.group}:{item.label} -> {item.is_active}')
        return jsonify({'success': True, 'is_active': item.is_active})

    @app.route('/lookups/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_lookup(id):
        if current_user.role != 'admin':
            flash('دسترسی غیرمجاز.', 'error')
            return redirect(url_for('dashboard'))
        
        item = LookupItem.query.get_or_404(id)
        
        if request.method == 'POST':
            item.group = request.form.get('group') or item.group
            item.key = request.form.get('key') or request.form.get('label')
            item.label = request.form.get('label')
            item.order = int(request.form.get('order') or 0)
            
            if not item.label:
                flash('برچسب الزامی است', 'error')
                return redirect(url_for('edit_lookup', id=id))
            
            db.session.commit()
            app.log_activity('update', 'LookupItem', item.id, 200, f'Edit {item.group}:{item.label}')
            flash('آیتم با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('lookups', group=item.group))
        
        return render_template('edit_lookup.html', item=item)

    @app.route('/lookups/<int:id>/delete', methods=['POST'])
    @login_required
    def delete_lookup(id):
        if current_user.role != 'admin':
            return jsonify({'success': False})
        item = LookupItem.query.get_or_404(id)
        group = item.group
        db.session.delete(item)
        db.session.commit()
        app.log_activity('delete', 'LookupItem', id, 200, f'Delete {group}:{item.label}')
        return jsonify({'success': True})

    @app.route('/people')
    @login_required
    def people():
        if current_user.role != 'admin':
            flash('دسترسی غیرمجاز.', 'error')
            return redirect(url_for('dashboard'))
        page = request.args.get('page', 1, type=int)
        category = request.args.get('category', 'internal')
        q = request.args.get('q', '')
        query = Person.query
        if category in ('internal', 'external'):
            query = query.filter_by(category=category)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Person.username.ilike(like), Person.dongle_name.ilike(like), Person.phone.ilike(like), Person.department.ilike(like)))
        people_page = query.order_by(Person.updated_at.desc(), Person.created_at.desc()).paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('people.html', people=people_page, category=category, q=q)

    @app.route('/people/add', methods=['GET', 'POST'])
    @login_required
    def add_person():
        if current_user.role != 'admin':
            flash('دسترسی غیرمجاز.', 'error')
            return redirect(url_for('people'))
        form = PersonForm()
        # fill department choices from lookups
        departments = LookupItem.query.filter_by(group='department', is_active=True).order_by(LookupItem.order.asc(), LookupItem.label.asc()).all()
        form.department.choices = [('', 'انتخاب واحد/اداره')] + [(d.key, d.label) for d in departments]
        if form.validate_on_submit():
            person = Person(
                category=form.category.data,
                username=form.username.data,
                dongle_name=form.dongle_name.data or None,
                phone=form.phone.data or None,
                department=form.department.data or None,
                description=form.description.data or None,
                created_by=current_user.id
            )
            db.session.add(person)
            db.session.commit()
            app.log_activity('create', 'Person', person.id, 200, f'Add person {person.username}')
            flash('کاربر سامانه با موفقیت افزوده شد.', 'success')
            return redirect(url_for('people', category=person.category))
        return render_template('add_person.html', form=form)

    @app.route('/people/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_person(id):
        if current_user.role != 'admin':
            flash('دسترسی غیرمجاز.', 'error')
            return redirect(url_for('people'))
        person = Person.query.get_or_404(id)
        form = PersonEditForm(obj=person)
        departments = LookupItem.query.filter_by(group='department', is_active=True).order_by(LookupItem.order.asc(), LookupItem.label.asc()).all()
        form.department.choices = [('', 'انتخاب واحد/اداره')] + [(d.key, d.label) for d in departments]
        if form.validate_on_submit():
            person.category = form.category.data
            person.username = form.username.data
            person.dongle_name = form.dongle_name.data or None
            person.phone = form.phone.data or None
            person.department = form.department.data or None
            person.description = form.description.data or None
            db.session.commit()
            app.log_activity('update', 'Person', person.id, 200, f'Edit person {person.username}')
            flash('به‌روزرسانی با موفقیت انجام شد.', 'success')
            return redirect(url_for('people', category=person.category))
        return render_template('edit_person.html', form=form, person=person)

    @app.route('/people/delete/<int:id>', methods=['POST'])
    @login_required
    @csrf.exempt
    def delete_person(id):
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'دسترسی غیرمجاز'})
        person = Person.query.get_or_404(id)
        db.session.delete(person)
        db.session.commit()
        app.log_activity('delete', 'Person', id, 200, f'Delete person {person.username}')
        return jsonify({'success': True})

    @app.route('/bookmarks/add', methods=['GET', 'POST'])
    @login_required
    def add_bookmark():
        form = BookmarkForm()
        if form.validate_on_submit():
            # اگر neither url nor address ارائه نشده، خطا
            if not form.url.data and not form.address.data:
                flash('حداقل یکی از فیلدهای "آدرس/دامنه" یا "لینک کامل" را وارد کنید.', 'error')
                return render_template('add_bookmark.html', form=form)

            bookmark = Bookmark(
                name=form.name.data,
                address=form.address.data or None,
                port=form.port.data if form.port.data else None,
                url=form.url.data or None,
                description=form.description.data or None,
                is_favorite=form.is_favorite.data or False,
                created_by=current_user.id
            )
            db.session.add(bookmark)
            db.session.commit()
            flash('بوکمارک با موفقیت اضافه شد.', 'success')
            return redirect(url_for('bookmarks'))
        return render_template('add_bookmark.html', form=form)

    @app.route('/bookmarks/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_bookmark(id):
        bookmark = Bookmark.query.filter_by(id=id, created_by=current_user.id).first_or_404()
        form = BookmarkEditForm(obj=bookmark)
        if form.validate_on_submit():
            if not form.url.data and not form.address.data:
                flash('حداقل یکی از فیلدهای "آدرس/دامنه" یا "لینک کامل" را وارد کنید.', 'error')
                return render_template('edit_bookmark.html', form=form, bookmark=bookmark)

            bookmark.name = form.name.data
            bookmark.address = form.address.data or None
            bookmark.port = form.port.data if form.port.data else None
            bookmark.url = form.url.data or None
            bookmark.description = form.description.data or None
            bookmark.is_favorite = form.is_favorite.data or False
            bookmark.updated_at = datetime.utcnow()
            db.session.commit()
            flash('بوکمارک با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('bookmarks'))
        return render_template('edit_bookmark.html', form=form, bookmark=bookmark)

    @app.route('/bookmarks/delete/<int:id>', methods=['POST'])
    @login_required
    @csrf.exempt
    def delete_bookmark(id):
        bookmark = Bookmark.query.filter_by(id=id, created_by=current_user.id).first_or_404()
        db.session.delete(bookmark)
        db.session.commit()
        flash('بوکمارک حذف شد.', 'success')
        return redirect(url_for('bookmarks'))
    
    # Credential Management Routes
    @app.route('/credentials')
    @login_required
    def credentials():
        page = request.args.get('page', 1, type=int)
        search_form = CredentialSearchForm()
        
        # فیلترها
        query = request.args.get('query', '')
        service_type = request.args.get('service_type', '')
        tags = request.args.get('tags', '')
        
        # ساخت کوئری
        credentials_query = Credential.query.filter_by(created_by=current_user.id)
        
        if query:
            credentials_query = credentials_query.filter(
                Credential.name.contains(query) | 
                Credential.username.contains(query) |
                Credential.description.contains(query)
            )
        
        if service_type:
            credentials_query = credentials_query.filter_by(service_type=service_type)
        
        if tags:
            credentials_query = credentials_query.filter(Credential.tags.contains(tags))
        
        credentials = credentials_query.order_by(Credential.updated_at.desc()).paginate(
            page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        
        return render_template('credentials.html', credentials=credentials, search_form=search_form)
    
    @app.route('/credentials/add', methods=['GET', 'POST'])
    @login_required
    def add_credential():
        form = CredentialForm()
        if form.validate_on_submit():
            credential = Credential(
                name=form.name.data,
                service_type=form.service_type.data,
                username=form.username.data,
                url=form.url.data,
                description=form.description.data,
                is_active=form.is_active.data,
                created_by=current_user.id
            )
            credential.set_password(form.password.data)
            credential.set_tags_list([tag.strip() for tag in form.tags.data.split(',') if tag.strip()])
            
            db.session.add(credential)
            db.session.commit()
            flash('رمز عبور با موفقیت اضافه شد.', 'success')
            return redirect(url_for('credentials'))
        
        return render_template('add_credential.html', form=form)
    
    @app.route('/credentials/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_credential(id):
        credential = Credential.query.filter_by(id=id, created_by=current_user.id).first_or_404()
        form = CredentialEditForm(obj=credential)
        
        # تنظیم برچسب‌ها
        form.tags.data = ', '.join(credential.get_tags_list())
        
        if form.validate_on_submit():
            credential.name = form.name.data
            credential.service_type = form.service_type.data
            credential.username = form.username.data
            credential.url = form.url.data
            credential.description = form.description.data
            credential.is_active = form.is_active.data
            
            # تغییر رمز عبور اگر ارائه شده
            if form.password.data:
                credential.set_password(form.password.data)
            
            credential.set_tags_list([tag.strip() for tag in form.tags.data.split(',') if tag.strip()])
            credential.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('رمز عبور با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('credentials'))
        
        return render_template('edit_credential.html', form=form, credential=credential)
    
    @app.route('/credentials/delete/<int:id>', methods=['POST'])
    @login_required
    @csrf.exempt
    def delete_credential(id):
        credential = Credential.query.filter_by(id=id, created_by=current_user.id).first_or_404()
        db.session.delete(credential)
        db.session.commit()
        flash('رمز عبور با موفقیت حذف شد.', 'success')
        return redirect(url_for('credentials'))
    
    @app.route('/credentials/view/<int:id>')
    @login_required
    def view_credential(id):
        credential = Credential.query.filter_by(id=id, created_by=current_user.id).first_or_404()
        return render_template('view_credential.html', credential=credential)
    
    @app.route('/api/credentials/<int:id>/password')
    @login_required
    def get_credential_password(id):
        credential = Credential.query.filter_by(id=id, created_by=current_user.id).first_or_404()
        # در اینجا باید رمز عبور را رمزگشایی کنیم - این یک پیاده‌سازی ساده است
        # در واقعیت باید از کلیدهای رمزنگاری استفاده کنید
        return jsonify({'password': 'رمز عبور رمزنگاری شده است'})
    
    @app.route('/api/credentials/<int:id>/use', methods=['POST'])
    @login_required
    def mark_credential_used(id):
        credential = Credential.query.filter_by(id=id, created_by=current_user.id).first_or_404()
        credential.last_used = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    
    # Helper function to get custom fields for records
    def get_custom_fields_for_records(records, model_name):
        """دریافت فیلدهای سفارشی برای لیست رکوردها"""
        if not records:
            return {}
        
        # دریافت فیلدهای سفارشی فعال برای مدل
        custom_fields = CustomField.query.filter_by(
            model_name=model_name, 
            is_active=True
        ).order_by(CustomField.order).all()
        
        if not custom_fields:
            return {}
        
        # دریافت مقادیر فیلدهای سفارشی
        record_ids = [record.id for record in records]
        custom_values = CustomFieldValue.query.filter(
            CustomFieldValue.model_name == model_name,
            CustomFieldValue.record_id.in_(record_ids)
        ).all()
        
        # سازماندهی داده‌ها
        result = {}
        for record in records:
            result[record.id] = {}
            for field in custom_fields:
                # پیدا کردن مقدار فیلد برای این رکورد
                field_value = next(
                    (cv for cv in custom_values if cv.field_id == field.id and cv.record_id == record.id),
                    None
                )
                result[record.id][field.name] = {
                    'label': field.label,
                    'value': field_value.value if field_value else '',
                    'field_type': field.field_type
                }
        
        return result

    # Helper function to get custom fields structure for templates
    def get_custom_fields_structure(custom_fields_data):
        """دریافت ساختار فیلدهای سفارشی برای template"""
        if not custom_fields_data:
            return []
        
        # پیدا کردن اولین رکورد که فیلدهای سفارشی دارد
        for record_id, fields in custom_fields_data.items():
            if fields:
                return list(fields.items())
        
        return []

    # User Profile Routes
    @app.route('/profile')
    @login_required
    def profile():
        # آمار شخصی کاربر
        user_stats = {
            'tasks_count': Task.query.filter_by(assigned_to=current_user.id).count(),
            'completed_tasks': Task.query.filter_by(assigned_to=current_user.id, status='completed').count(),
            'pending_tasks': Task.query.filter_by(assigned_to=current_user.id, status='pending').count(),
            'credentials_count': Credential.query.filter_by(created_by=current_user.id).count(),
            'notifications_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        }
        
        # آخرین فعالیت‌ها
        recent_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.created_at.desc()).limit(5).all()
        recent_credentials = Credential.query.filter_by(created_by=current_user.id).order_by(Credential.created_at.desc()).limit(5).all()
        
        return render_template('profile.html', 
                             user_stats=user_stats, 
                             recent_tasks=recent_tasks, 
                             recent_credentials=recent_credentials)
    
    @app.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        form = EditUserForm(obj=current_user)
        
        if form.validate_on_submit():
            # بررسی تکراری نبودن ایمیل
            existing_user = User.query.filter(User.email == form.email.data, User.id != current_user.id).first()
            if existing_user:
                flash('ایمیل قبلاً استفاده شده است.', 'error')
                return render_template('edit_profile.html', form=form)
            
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('پروفایل با موفقیت به‌روزرسانی شد.', 'success')
            return redirect(url_for('profile'))
        
        return render_template('edit_profile.html', form=form)
    
    @app.route('/profile/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        form = ChangePasswordForm()
        
        if form.validate_on_submit():
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                db.session.commit()
                flash('رمز عبور با موفقیت تغییر کرد.', 'success')
                return redirect(url_for('profile'))
            else:
                flash('رمز عبور فعلی اشتباه است.', 'error')
        
        return render_template('change_password.html', form=form)
    
    @app.route('/profile/credentials')
    @login_required
    def personal_credentials():
        """رمزهای شخصی کاربر"""
        page = request.args.get('page', 1, type=int)
        search_form = CredentialSearchForm()
        
        # فیلترها
        query = request.args.get('query', '')
        service_type = request.args.get('service_type', '')
        tags = request.args.get('tags', '')
        
        # ساخت کوئری - فقط رمزهای شخصی کاربر
        credentials_query = Credential.query.filter_by(created_by=current_user.id)
        
        if query:
            credentials_query = credentials_query.filter(
                or_(
                    Credential.name.contains(query),
                    Credential.description.contains(query),
                    Credential.username.contains(query)
                )
            )
        
        if service_type:
            credentials_query = credentials_query.filter_by(service_type=service_type)
        
        if tags:
            credentials_query = credentials_query.filter(Credential.tags.contains(tags))
        
        credentials = credentials_query.order_by(Credential.created_at.desc()).paginate(
            page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        
        return render_template('personal_credentials.html', 
                             credentials=credentials, 
                             search_form=search_form,
                             query=query,
                             service_type=service_type,
                             tags=tags)
    
    @app.route('/profile/credentials/add', methods=['GET', 'POST'])
    @login_required
    def add_personal_credential():
        """اضافه کردن رمز شخصی"""
        form = CredentialForm()
        
        if form.validate_on_submit():
            credential = Credential(
                name=form.name.data,
                service_type=form.service_type.data,
                username=form.username.data,
                url=form.url.data,
                description=form.description.data,
                created_by=current_user.id
            )
            
            # تنظیم پسورد
            credential.set_password(form.password.data)
            
            # تنظیم برچسب‌ها
            if form.tags.data:
                credential.set_tags_list([tag.strip() for tag in form.tags.data.split(',')])
            
            db.session.add(credential)
            db.session.commit()
            flash('رمز عبور شخصی با موفقیت اضافه شد.', 'success')
            return redirect(url_for('personal_credentials'))
        
        return render_template('add_personal_credential.html', form=form)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # FreeIPA Routes
    @app.route('/freeipa')
    @login_required
    def freeipa_dashboard():
        """داشبورد FreeIPA"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            
            # آمار کلی
            total_users = db.session.query(FreeIPAUser).count()
            total_groups = db.session.query(FreeIPAGroup).count()
            active_servers = db.session.query(FreeIPAServer).filter_by(is_active=True).count()
            
            # آخرین فعالیت‌ها
            recent_users = db.session.query(FreeIPAUser).order_by(FreeIPAUser.created_at.desc()).limit(5).all()
            recent_sms = db.session.query(SMSLog).order_by(SMSLog.created_at.desc()).limit(5).all()
            
            return render_template('freeipa/dashboard.html',
                                 total_users=total_users,
                                 total_groups=total_groups,
                                 active_servers=active_servers,
                                 recent_users=recent_users,
                                 recent_sms=recent_sms)
        except Exception as e:
            flash(f'خطا در بارگذاری داشبورد FreeIPA: {str(e)}', 'error')
            return redirect(url_for('dashboard'))
    
    @app.route('/freeipa/servers')
    @login_required
    def freeipa_servers():
        """لیست سرورهای FreeIPA"""
        servers = db.session.query(FreeIPAServer).all()
        return render_template('freeipa/servers.html', servers=servers)
    
    @app.route('/freeipa/servers/add', methods=['GET', 'POST'])
    @login_required
    def freeipa_add_server():
        """اضافه کردن سرور FreeIPA"""
        if request.method == 'POST':
            try:
                server = FreeIPAServer(
                    name=request.form['name'],
                    hostname=request.form['hostname'],
                    port=int(request.form['port']),
                    use_ssl=bool(request.form.get('use_ssl')),
                    base_dn=request.form['base_dn'],
                    bind_dn=request.form['bind_dn']
                )
                server.set_bind_password(request.form['bind_password'])
                
                db.session.add(server)
                db.session.commit()
                
                flash('سرور FreeIPA با موفقیت اضافه شد', 'success')
                return redirect(url_for('freeipa_servers'))
            except Exception as e:
                db.session.rollback()
                flash(f'خطا در اضافه کردن سرور: {str(e)}', 'error')
        
        return render_template('freeipa/add_server.html')
    
    @app.route('/freeipa/servers/test/<int:server_id>')
    @login_required
    def freeipa_test_server(server_id):
        """تست اتصال سرور FreeIPA"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            success, message = freeipa_manager.test_connection(server_id)
            
            if success:
                flash('اتصال به سرور موفقیت‌آمیز بود', 'success')
            else:
                flash(f'خطا در اتصال: {message}', 'error')
        except Exception as e:
            flash(f'خطا در تست اتصال: {str(e)}', 'error')
        
        return redirect(url_for('freeipa_servers'))
    
    @app.route('/freeipa/servers/edit/<int:server_id>', methods=['GET', 'POST'])
    @login_required
    def freeipa_edit_server(server_id):
        """ویرایش سرور FreeIPA"""
        server = db.session.query(FreeIPAServer).get_or_404(server_id)
        
        if request.method == 'POST':
            try:
                server.name = request.form['name']
                server.hostname = request.form['hostname']
                server.port = int(request.form['port'])
                server.use_ssl = bool(request.form.get('use_ssl'))
                server.base_dn = request.form['base_dn']
                server.bind_dn = request.form['bind_dn']
                server.is_active = bool(request.form.get('is_active'))
                
                # تغییر پسورد اگر ارائه شده
                new_password = request.form.get('bind_password')
                if new_password:
                    server.set_bind_password(new_password)
                
                db.session.commit()
                flash('سرور با موفقیت به‌روزرسانی شد', 'success')
                return redirect(url_for('freeipa_servers'))
            except Exception as e:
                db.session.rollback()
                flash(f'خطا در به‌روزرسانی سرور: {str(e)}', 'error')
        
        return render_template('freeipa/edit_server.html', server=server)
    
    @app.route('/freeipa/servers/delete/<int:server_id>', methods=['POST'])
    @login_required
    def freeipa_delete_server(server_id):
        """حذف سرور FreeIPA"""
        try:
            server = db.session.query(FreeIPAServer).get_or_404(server_id)
            db.session.delete(server)
            db.session.commit()
            flash('سرور با موفقیت حذف شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در حذف سرور: {str(e)}', 'error')
        
        return redirect(url_for('freeipa_servers'))
    
    @app.route('/freeipa/users')
    @login_required
    def freeipa_users():
        """لیست کاربران FreeIPA"""
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        users = db.session.query(FreeIPAUser).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('freeipa/users.html', users=users)
    
    @app.route('/freeipa/users/add', methods=['GET', 'POST'])
    @login_required
    def freeipa_add_user():
        """اضافه کردن کاربر FreeIPA"""
        if request.method == 'POST':
            try:
                freeipa_manager = FreeIPAManager(db.session)
                
                # دریافت گروه‌ها
                groups = request.form.getlist('groups')
                
                success, message, password = freeipa_manager.create_user(
                    uid=request.form['uid'],
                    cn=request.form['cn'],
                    sn=request.form['sn'],
                    givenname=request.form['givenname'],
                    mail=request.form['mail'],
                    mobile=request.form.get('mobile'),
                    groups=groups,
                    send_sms=bool(request.form.get('send_sms'))
                )
                
                if success:
                    flash(f'کاربر با موفقیت ایجاد شد. رمز عبور: {password}', 'success')
                    return redirect(url_for('freeipa_users'))
                else:
                    flash(f'خطا در ایجاد کاربر: {message}', 'error')
            except Exception as e:
                flash(f'خطا در ایجاد کاربر: {str(e)}', 'error')
        
        # دریافت لیست گروه‌ها
        groups = db.session.query(FreeIPAGroup).filter_by(is_active=True).all()
        return render_template('freeipa/add_user.html', groups=groups)
    
    @app.route('/freeipa/users/edit/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    def freeipa_edit_user(user_id):
        """ویرایش کاربر FreeIPA"""
        user = db.session.query(FreeIPAUser).get_or_404(user_id)
        
        if request.method == 'POST':
            try:
                freeipa_manager = FreeIPAManager(db.session)
                
                success, message = freeipa_manager.update_user(
                    user_id=user_id,
                    cn=request.form['cn'],
                    sn=request.form['sn'],
                    givenname=request.form['givenname'],
                    mail=request.form['mail'],
                    mobile=request.form.get('mobile')
                )
                
                if success:
                    flash('کاربر با موفقیت به‌روزرسانی شد', 'success')
                    return redirect(url_for('freeipa_users'))
                else:
                    flash(f'خطا در به‌روزرسانی: {message}', 'error')
            except Exception as e:
                flash(f'خطا در به‌روزرسانی: {str(e)}', 'error')
        
        return render_template('freeipa/edit_user.html', user=user)
    
    @app.route('/freeipa/users/change-password/<int:user_id>', methods=['POST'])
    @login_required
    def freeipa_change_password(user_id):
        """تغییر پسورد کاربر FreeIPA"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            
            new_password = request.form.get('new_password')
            send_sms = bool(request.form.get('send_sms'))
            
            success, message, password = freeipa_manager.change_password(
                user_id=user_id,
                new_password=new_password,
                send_sms=send_sms
            )
            
            if success:
                flash(f'پسورد با موفقیت تغییر کرد. رمز جدید: {password}', 'success')
            else:
                flash(f'خطا در تغییر پسورد: {message}', 'error')
        except Exception as e:
            flash(f'خطا در تغییر پسورد: {str(e)}', 'error')
        
        return redirect(url_for('freeipa_users'))
    
    @app.route('/freeipa/users/passwords/<int:user_id>')
    @login_required
    def freeipa_user_passwords(user_id):
        """لیست پسوردهای کاربر"""
        user = db.session.query(FreeIPAUser).get_or_404(user_id)
        freeipa_manager = FreeIPAManager(db.session)
        passwords = freeipa_manager.get_user_passwords(user_id)
        
        return render_template('freeipa/user_passwords.html', user=user, passwords=passwords)
    
    @app.route('/freeipa/users/resend-sms/<int:password_id>', methods=['POST'])
    @login_required
    def freeipa_resend_sms(password_id):
        """ارسال مجدد پیامک پسورد"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            success, message = freeipa_manager.resend_password_sms(password_id)
            
            if success:
                flash('پیامک با موفقیت ارسال شد', 'success')
            else:
                flash(f'خطا در ارسال پیامک: {message}', 'error')
        except Exception as e:
            flash(f'خطا در ارسال پیامک: {str(e)}', 'error')
        
        return redirect(request.referrer or url_for('freeipa_users'))
    
    @app.route('/freeipa/groups')
    @login_required
    def freeipa_groups():
        """لیست گروه‌های FreeIPA"""
        groups = db.session.query(FreeIPAGroup).all()
        return render_template('freeipa/groups.html', groups=groups)
    
    @app.route('/freeipa/groups/add', methods=['GET', 'POST'])
    @login_required
    def freeipa_add_group():
        """اضافه کردن گروه FreeIPA"""
        if request.method == 'POST':
            try:
                freeipa_manager = FreeIPAManager(db.session)
                
                success, message = freeipa_manager.create_group(
                    cn=request.form['cn'],
                    description=request.form.get('description')
                )
                
                if success:
                    flash('گروه با موفقیت ایجاد شد', 'success')
                    return redirect(url_for('freeipa_groups'))
                else:
                    flash(f'خطا در ایجاد گروه: {message}', 'error')
            except Exception as e:
                flash(f'خطا در ایجاد گروه: {str(e)}', 'error')
        
        return render_template('freeipa/add_group.html')
    
    @app.route('/freeipa/groups/edit/<int:group_id>', methods=['GET', 'POST'])
    @login_required
    def freeipa_edit_group(group_id):
        """ویرایش گروه FreeIPA"""
        group = FreeIPAGroup.query.get_or_404(group_id)
        
        if request.method == 'POST':
            try:
                group.cn = request.form['cn']
                group.description = request.form.get('description')
                group.is_active = 'is_active' in request.form
                
                db.session.commit()
                flash('گروه با موفقیت ویرایش شد', 'success')
                return redirect(url_for('freeipa_groups'))
            except Exception as e:
                flash(f'خطا در ویرایش گروه: {str(e)}', 'error')
        
        return render_template('freeipa/edit_group.html', group=group)
    
    @app.route('/freeipa/groups/delete/<int:group_id>', methods=['POST'])
    @login_required
    def freeipa_delete_group(group_id):
        """حذف گروه FreeIPA"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            success, message = freeipa_manager.delete_group(group_id)
            
            if success:
                flash('گروه با موفقیت حذف شد', 'success')
            else:
                flash(f'خطا در حذف گروه: {message}', 'error')
        except Exception as e:
            flash(f'خطا در حذف گروه: {str(e)}', 'error')
        
        return redirect(url_for('freeipa_groups'))
    
    @app.route('/freeipa/users/delete/<int:user_id>', methods=['POST'])
    @login_required
    def freeipa_delete_user(user_id):
        """حذف کاربر FreeIPA"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            success, message = freeipa_manager.delete_user(user_id)
            
            if success:
                flash('کاربر با موفقیت حذف شد', 'success')
            else:
                flash(f'خطا در حذف کاربر: {message}', 'error')
        except Exception as e:
            flash(f'خطا در حذف کاربر: {str(e)}', 'error')
        
        return redirect(url_for('freeipa_users'))
    
    @app.route('/freeipa/users/add-to-group/<int:user_id>', methods=['POST'])
    @login_required
    def freeipa_add_user_to_group(user_id):
        """اضافه کردن کاربر به گروه"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            
            group_cn = request.form['group_cn']
            success, message = freeipa_manager.add_user_to_group(user_id, group_cn)
            
            if success:
                flash('کاربر با موفقیت به گروه اضافه شد', 'success')
            else:
                flash(f'خطا در اضافه کردن به گروه: {message}', 'error')
        except Exception as e:
            flash(f'خطا در اضافه کردن به گروه: {str(e)}', 'error')
        
        return redirect(request.referrer or url_for('freeipa_users'))
    
    @app.route('/freeipa/users/remove-from-group/<int:user_id>', methods=['POST'])
    @login_required
    def freeipa_remove_user_from_group(user_id):
        """حذف کاربر از گروه"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            
            group_cn = request.form['group_cn']
            success, message = freeipa_manager.remove_user_from_group(user_id, group_cn)
            
            if success:
                flash('کاربر با موفقیت از گروه حذف شد', 'success')
            else:
                flash(f'خطا در حذف از گروه: {message}', 'error')
        except Exception as e:
            flash(f'خطا در حذف از گروه: {str(e)}', 'error')
        
        return redirect(request.referrer or url_for('freeipa_users'))
    
    @app.route('/freeipa/sync')
    @login_required
    def freeipa_sync():
        """همگام‌سازی با FreeIPA"""
        try:
            freeipa_manager = FreeIPAManager(db.session)
            success, message = freeipa_manager.sync_users_from_freeipa()
            
            if success:
                flash(message, 'success')
            else:
                flash(f'خطا در همگام‌سازی: {message}', 'error')
        except Exception as e:
            flash(f'خطا در همگام‌سازی: {str(e)}', 'error')
        
        return redirect(url_for('freeipa_dashboard'))
    
    @app.route('/freeipa/sms-templates')
    @login_required
    def freeipa_sms_templates():
        """لیست قالب‌های پیامک"""
        templates = db.session.query(SMSTemplate).all()
        return render_template('freeipa/sms_templates.html', templates=templates)
    
    @app.route('/freeipa/sms-templates/add', methods=['GET', 'POST'])
    @login_required
    def freeipa_add_sms_template():
        """اضافه کردن قالب پیامک"""
        if request.method == 'POST':
            try:
                template = SMSTemplate(
                    name=request.form['name'],
                    template=request.form['template'],
                    is_active=bool(request.form.get('is_active'))
                )
                
                # تنظیم متغیرها
                variables = request.form.getlist('variables')
                template.set_variables_list(variables)
                
                db.session.add(template)
                db.session.commit()
                
                flash('قالب پیامک با موفقیت اضافه شد', 'success')
                return redirect(url_for('freeipa_sms_templates'))
            except Exception as e:
                db.session.rollback()
                flash(f'خطا در اضافه کردن قالب: {str(e)}', 'error')
        
        return render_template('freeipa/add_sms_template.html')
    
    @app.route('/freeipa/sms-logs')
    @login_required
    def freeipa_sms_logs():
        """لاگ‌های ارسال پیامک"""
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        logs = db.session.query(SMSLog).order_by(SMSLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('freeipa/sms_logs.html', logs=logs)
    
    @app.route('/freeipa/sms-templates/edit/<int:template_id>', methods=['GET', 'POST'])
    @login_required
    def freeipa_edit_sms_template(template_id):
        """ویرایش قالب پیامک"""
        template = db.session.query(SMSTemplate).get_or_404(template_id)
        
        if request.method == 'POST':
            try:
                template.name = request.form['name']
                template.template = request.form['template']
                template.is_active = bool(request.form.get('is_active'))
                
                db.session.commit()
                flash('قالب با موفقیت به‌روزرسانی شد', 'success')
                return redirect(url_for('freeipa_sms_templates'))
            except Exception as e:
                db.session.rollback()
                flash(f'خطا در به‌روزرسانی قالب: {str(e)}', 'error')
        
        return render_template('freeipa/edit_sms_template.html', template=template)
    
    @app.route('/freeipa/sms-templates/delete/<int:template_id>', methods=['POST'])
    @login_required
    def freeipa_delete_sms_template(template_id):
        """حذف قالب پیامک"""
        try:
            template = db.session.query(SMSTemplate).get_or_404(template_id)
            db.session.delete(template)
            db.session.commit()
            flash('قالب با موفقیت حذف شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در حذف قالب: {str(e)}', 'error')
        
        return redirect(url_for('freeipa_sms_templates'))
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
