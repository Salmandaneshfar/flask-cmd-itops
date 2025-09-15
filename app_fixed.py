from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import sqlite3

from config import config
from models import db, User, Server, Task, Content, Backup, CustomField, CustomFieldValue
from forms import (LoginForm, UserForm, EditUserForm, ChangePasswordForm, 
                  ServerForm, TaskForm, ContentForm, BackupForm, SearchForm,
                  CustomFieldForm, CustomFieldEditForm)

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'لطفاً ابتدا وارد شوید.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
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
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('نام کاربری یا رمز عبور اشتباه است.', 'error')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
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
        users = User.query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('users.html', users=users)
    
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
            db.session.commit()
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
            db.session.commit()
            flash('کاربر با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('users'))
        
        return render_template('edit_user.html', form=form, user=user)
    
    # Server management routes
    @app.route('/servers')
    @login_required
    def servers():
        page = request.args.get('page', 1, type=int)
        servers = Server.query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('servers.html', servers=servers)
    
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
            db.session.commit()
            flash('سرور با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('servers'))
        
        return render_template('edit_server.html', form=form, server=server)
    
    # Task management routes
    @app.route('/tasks')
    @login_required
    def tasks():
        page = request.args.get('page', 1, type=int)
        tasks = Task.query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('tasks.html', tasks=tasks)
    
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
            db.session.commit()
            flash('تسک با موفقیت اضافه شد.', 'success')
            return redirect(url_for('tasks'))
        
        return render_template('add_task.html', form=form)
    
    # Content management routes
    @app.route('/content')
    @login_required
    def content():
        page = request.args.get('page', 1, type=int)
        content = Content.query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
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
    
    # Backup management routes
    @app.route('/backups')
    @login_required
    def backups():
        page = request.args.get('page', 1, type=int)
        backups = Backup.query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('backups.html', backups=backups)
    
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
    
    # Custom Fields Management
    @app.route('/custom-fields')
    @login_required
    def custom_fields():
        if current_user.role != 'admin':
            flash('شما دسترسی لازم را ندارید.', 'error')
            return redirect(url_for('dashboard'))
        
        page = request.args.get('page', 1, type=int)
        fields = CustomField.query.order_by(CustomField.model_name, CustomField.order).paginate(
            page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('custom_fields.html', fields=fields)
    
    @app.route('/custom-fields/add', methods=['GET', 'POST'])
    @login_required
    def add_custom_field():
        if current_user.role != 'admin':
            flash('شما دسترسی لازم را ندارید.', 'error')
            return redirect(url_for('custom_fields'))
        
        form = CustomFieldForm()
        if form.validate_on_submit():
            # بررسی تکراری نبودن نام فیلد
            existing_field = CustomField.query.filter_by(
                name=form.name.data, 
                model_name=form.model_name.data
            ).first()
            
            if existing_field:
                flash('فیلد با این نام قبلاً برای این مدل تعریف شده است.', 'error')
                return render_template('add_custom_field.html', form=form)
            
            field = CustomField(
                name=form.name.data,
                label=form.label.data,
                field_type=form.field_type.data,
                model_name=form.model_name.data,
                is_required=form.is_required.data,
                is_active=form.is_active.data,
                placeholder=form.placeholder.data,
                help_text=form.help_text.data,
                order=int(form.order.data) if form.order.data else 0
            )
            
            # پردازش گزینه‌های انتخابی
            if form.options.data and form.field_type.data == 'select':
                options_list = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()]
                field.set_options(options_list)
            
            db.session.add(field)
            db.session.commit()
            flash('فیلد سفارشی با موفقیت اضافه شد.', 'success')
            return redirect(url_for('custom_fields'))
        
        return render_template('add_custom_field.html', form=form)
    
    @app.route('/custom-fields/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_custom_field(id):
        if current_user.role != 'admin':
            flash('شما دسترسی لازم را ندارید.', 'error')
            return redirect(url_for('custom_fields'))
        
        field = CustomField.query.get_or_404(id)
        form = CustomFieldEditForm(obj=field)
        
        # نمایش گزینه‌های موجود
        if field.field_type == 'select' and field.options:
            form.options.data = '\n'.join(field.get_options())
        
        if form.validate_on_submit():
            field.label = form.label.data
            field.field_type = form.field_type.data
            field.is_required = form.is_required.data
            field.is_active = form.is_active.data
            field.placeholder = form.placeholder.data
            field.help_text = form.help_text.data
            field.order = int(form.order.data) if form.order.data else 0
            
            # پردازش گزینه‌های انتخابی
            if form.options.data and form.field_type.data == 'select':
                options_list = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()]
                field.set_options(options_list)
            else:
                field.options = None
            
            db.session.commit()
            flash('فیلد سفارشی با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('custom_fields'))
        
        return render_template('edit_custom_field.html', form=form, field=field)
    
    @app.route('/custom-fields/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_custom_field(id):
        if current_user.role != 'admin':
            flash('شما دسترسی لازم را ندارید.', 'error')
            return redirect(url_for('custom_fields'))
        
        field = CustomField.query.get_or_404(id)
        
        # حذف مقادیر مربوطه
        CustomFieldValue.query.filter_by(field_id=id).delete()
        
        db.session.delete(field)
        db.session.commit()
        flash('فیلد سفارشی با موفقیت حذف شد.', 'success')
        return redirect(url_for('custom_fields'))
    
    # API for dynamic field values
    @app.route('/api/custom-field-value', methods=['POST'])
    @login_required
    def save_custom_field_value():
        data = request.get_json()
        field_id = data.get('field_id')
        model_name = data.get('model_name')
        record_id = data.get('record_id')
        value = data.get('value')
        
        # پیدا کردن یا ایجاد مقدار فیلد
        field_value = CustomFieldValue.query.filter_by(
            field_id=field_id,
            model_name=model_name,
            record_id=record_id
        ).first()
        
        if field_value:
            field_value.value = value
        else:
            field_value = CustomFieldValue(
                field_id=field_id,
                model_name=model_name,
                record_id=record_id,
                value=value
            )
            db.session.add(field_value)
        
        db.session.commit()
        return jsonify({'success': True})
    
    @app.route('/api/custom-field-values/<model_name>/<int:record_id>')
    @login_required
    def get_custom_field_values(model_name, record_id):
        values = CustomFieldValue.query.filter_by(
            model_name=model_name,
            record_id=record_id
        ).all()
        
        result = {}
        for value in values:
            result[value.field.name] = {
                'value': value.value,
                'field_type': value.field.field_type,
                'label': value.field.label
            }
        
        return jsonify(result)
    
    # API routes for AJAX
    @app.route('/api/task/<int:id>/status', methods=['POST'])
    @login_required
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
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
