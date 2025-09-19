#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت ایجاد فیلدهای تست برای بررسی عملکرد سیستم فیلدهای داینامیک
"""

from app import create_app
from models import db, CustomField

def create_test_fields():
    app = create_app()
    
    with app.app_context():
        # حذف فیلدهای تست قبلی
        CustomField.query.filter(CustomField.name.like('test_%')).delete(synchronize_session=False)
        db.session.commit()
        
        # فیلدهای تست برای مدل User
        test_fields = [
            {
                'name': 'test_text_field',
                'label': 'فیلد متنی تست',
                'field_type': 'text',
                'model_name': 'User',
                'is_required': True,
                'is_active': True,
                'placeholder': 'متن خود را وارد کنید',
                'help_text': 'این یک فیلد متنی تست است',
                'order': 1
            },
            {
                'name': 'test_number_field',
                'label': 'فیلد عددی تست',
                'field_type': 'number',
                'model_name': 'User',
                'is_required': False,
                'is_active': True,
                'placeholder': 'عدد وارد کنید',
                'help_text': 'یک عدد وارد کنید',
                'order': 3
            },
            {
                'name': 'test_email_field',
                'label': 'فیلد ایمیل تست',
                'field_type': 'email',
                'model_name': 'User',
                'is_required': False,
                'is_active': True,
                'placeholder': 'example@domain.com',
                'help_text': 'آدرس ایمیل معتبر وارد کنید',
                'order': 4
            },
            {
                'name': 'test_date_field',
                'label': 'فیلد تاریخ تست',
                'field_type': 'date',
                'model_name': 'User',
                'is_required': False,
                'is_active': True,
                'placeholder': '',
                'help_text': 'تاریخ را انتخاب کنید',
                'order': 5
            },
            {
                'name': 'test_textarea_field',
                'label': 'فیلد متن طولانی تست',
                'field_type': 'textarea',
                'model_name': 'User',
                'is_required': False,
                'is_active': True,
                'placeholder': 'متن طولانی خود را وارد کنید',
                'help_text': 'توضیحات کامل وارد کنید',
                'order': 6
            },
            {
                'name': 'test_checkbox_field',
                'label': 'فیلد چک باکس تست',
                'field_type': 'checkbox',
                'model_name': 'User',
                'is_required': False,
                'is_active': True,
                'placeholder': '',
                'help_text': 'در صورت موافقت تیک بزنید',
                'order': 7
            },
            # فیلدهای تست برای مدل Server
            {
                'name': 'test_server_location',
                'label': 'مکان سرور',
                'field_type': 'text',
                'model_name': 'Server',
                'is_required': True,
                'is_active': True,
                'placeholder': 'مکان فیزیکی سرور',
                'help_text': 'مکان فیزیکی سرور را وارد کنید',
                'order': 1
            },
            {
                'name': 'test_server_priority',
                'label': 'اولویت سرور',
                'field_type': 'text',
                'model_name': 'Server',
                'is_required': True,
                'is_active': True,
                'placeholder': 'اولویت سرور',
                'help_text': 'اولویت سرور را تعیین کنید',
                'order': 2
            },
            {
                'name': 'test_server_notes',
                'label': 'یادداشت‌های سرور',
                'field_type': 'textarea',
                'model_name': 'Server',
                'is_required': False,
                'is_active': True,
                'placeholder': 'یادداشت‌های مربوط به سرور',
                'help_text': 'اطلاعات اضافی در مورد سرور',
                'order': 3
            }
        ]
        
        created_fields = []
        
        for field_data in test_fields:
            field = CustomField(
                name=field_data['name'],
                label=field_data['label'],
                field_type=field_data['field_type'],
                model_name=field_data['model_name'],
                is_required=field_data['is_required'],
                is_active=field_data['is_active'],
                placeholder=field_data['placeholder'],
                help_text=field_data['help_text'],
                order=field_data['order']
            )
            
            
            db.session.add(field)
            created_fields.append(field)
        
        try:
            db.session.commit()
            print(f"✅ {len(created_fields)} فیلد تست با موفقیت ایجاد شد:")
            for field in created_fields:
                print(f"   - {field.name} ({field.label}) - {field.model_name}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در ایجاد فیلدهای تست: {e}")
            return False
        
        return True

if __name__ == '__main__':
    print("🚀 شروع ایجاد فیلدهای تست...")
    success = create_test_fields()
    if success:
        print("✅ فیلدهای تست با موفقیت ایجاد شدند!")
        print("🌐 برای تست به آدرس زیر بروید:")
        print("   http://127.0.0.1:5000/test-all-fields")
    else:
        print("❌ خطا در ایجاد فیلدهای تست!")
