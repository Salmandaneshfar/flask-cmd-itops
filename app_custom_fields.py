# Custom Fields Management - Rewritten
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, CustomField, CustomFieldValue
from forms import CustomFieldForm, CustomFieldEditForm
from sqlalchemy import or_

custom_fields_bp = Blueprint('custom_fields', __name__)

@custom_fields_bp.route('/custom-fields')
@login_required
def list_fields():
    """لیست فیلدهای سفارشی"""
    if current_user.role != 'admin':
        flash('شما دسترسی لازم را ندارید.', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    model_filter = request.args.get('model', '')
    type_filter = request.args.get('type', '')
    search = request.args.get('search', '')
    
    query = CustomField.query
    
    if model_filter:
        query = query.filter(CustomField.model_name == model_filter)
    if type_filter:
        query = query.filter(CustomField.field_type == type_filter)
    if search:
        query = query.filter(or_(
            CustomField.name.contains(search),
            CustomField.label.contains(search)
        ))
    
    fields = query.order_by(CustomField.model_name, CustomField.order).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('custom_fields_new.html', 
                         fields=fields, 
                         model_filter=model_filter,
                         type_filter=type_filter,
                         search=search)

@custom_fields_bp.route('/custom-fields/add', methods=['GET', 'POST'])
@login_required
def add_field():
    """اضافه کردن فیلد جدید"""
    if current_user.role != 'admin':
        flash('شما دسترسی لازم را ندارید.', 'error')
        return redirect(url_for('custom_fields.list_fields'))
    
    form = CustomFieldForm()
    if form.validate_on_submit():
        # بررسی تکراری نبودن نام فیلد
        existing = CustomField.query.filter_by(
            name=form.name.data,
            model_name=form.model_name.data
        ).first()
        
        if existing:
            flash('فیلد با این نام قبلاً برای این مدل تعریف شده است.', 'error')
            return render_template('add_custom_field_new.html', form=form)
        
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
        
        try:
            db.session.add(field)
            db.session.commit()
            flash('فیلد سفارشی با موفقیت اضافه شد.', 'success')
            return redirect(url_for('custom_fields.list_fields'))
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در ذخیره فیلد: {str(e)}', 'error')
    elif request.method == 'POST':
        # نمایش خطاهای اعتبارسنجی
        for field_name, field_errors in form.errors.items():
            for error in field_errors:
                flash(f'خطا در فیلد {field_name}: {error}', 'error')
    
    return render_template('add_custom_field_new.html', form=form)

@custom_fields_bp.route('/custom-fields/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_field(id):
    """ویرایش فیلد"""
    if current_user.role != 'admin':
        flash('شما دسترسی لازم را ندارید.', 'error')
        return redirect(url_for('custom_fields.list_fields'))
    
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
        if form.field_type.data == 'select':
            if form.options.data and form.options.data.strip():
                options_list = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()]
                field.set_options(options_list)
            else:
                field.options = None
        else:
            field.options = None
        
        try:
            db.session.commit()
            flash('فیلد سفارشی با موفقیت ویرایش شد.', 'success')
            return redirect(url_for('custom_fields.list_fields'))
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در ویرایش فیلد: {str(e)}', 'error')
    elif request.method == 'POST':
        # نمایش خطاهای اعتبارسنجی
        for field_name, field_errors in form.errors.items():
            for error in field_errors:
                flash(f'خطا در فیلد {field_name}: {error}', 'error')
    
    return render_template('edit_custom_field_new.html', form=form, field=field)

@custom_fields_bp.route('/custom-fields/delete/<int:id>', methods=['POST'])
@login_required
def delete_field(id):
    """حذف فیلد"""
    if current_user.role != 'admin':
        flash('شما دسترسی لازم را ندارید.', 'error')
        return redirect(url_for('custom_fields.list_fields'))
    
    field = CustomField.query.get_or_404(id)
    
    try:
        # حذف مقادیر مربوطه
        CustomFieldValue.query.filter_by(field_id=id).delete()
        db.session.delete(field)
        db.session.commit()
        flash('فیلد سفارشی با موفقیت حذف شد.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا در حذف فیلد: {str(e)}', 'error')
    
    return redirect(url_for('custom_fields.list_fields'))

@custom_fields_bp.route('/api/custom-fields/<model_name>')
@login_required
def get_fields_for_model(model_name):
    """دریافت فیلدهای یک مدل"""
    fields = CustomField.query.filter_by(
        model_name=model_name,
        is_active=True
    ).order_by(CustomField.order).all()
    
    result = []
    for field in fields:
        result.append({
            'id': field.id,
            'name': field.name,
            'label': field.label,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'placeholder': field.placeholder,
            'help_text': field.help_text,
            'options': field.get_options() if field.field_type == 'select' else None
        })
    
    return jsonify(result)

@custom_fields_bp.route('/api/custom-field-values/<model_name>/<int:record_id>')
@login_required
def get_field_values(model_name, record_id):
    """دریافت مقادیر فیلدهای یک رکورد"""
    values = CustomFieldValue.query.filter_by(
        model_name=model_name,
        record_id=record_id
    ).all()
    
    result = {}
    for value in values:
        result[value.field.name] = {
            'value': value.value,
            'field_type': value.field.field_type,
            'label': value.field.label,
            'field_id': value.field_id
        }
    
    return jsonify(result)

@custom_fields_bp.route('/api/custom-field-value', methods=['POST'])
@login_required
def save_field_value():
    """ذخیره مقدار فیلد"""
    data = request.get_json()
    field_id = data.get('field_id')
    model_name = data.get('model_name')
    record_id = data.get('record_id')
    value = data.get('value')
    
    if not all([field_id, model_name, record_id is not None]):
        return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
    
    try:
        # پیدا کردن یا ایجاد مقدار فیلد
        field_value = CustomFieldValue.query.filter_by(
            field_id=field_id,
            model_name=model_name,
            record_id=record_id
        ).first()
        
        if field_value:
            if value and value.strip():
                field_value.value = value.strip()
            else:
                # اگر مقدار خالی است، رکورد را حذف کن
                db.session.delete(field_value)
        else:
            if value and value.strip():
                field_value = CustomFieldValue(
                    field_id=field_id,
                    model_name=model_name,
                    record_id=record_id,
                    value=value.strip()
                )
                db.session.add(field_value)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
