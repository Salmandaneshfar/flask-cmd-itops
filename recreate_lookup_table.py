#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت ایجاد مجدد جدول lookup_item در دیتابیس
"""

from app import create_app
from models import db, LookupItem

def recreate_lookup_table():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 بررسی وجود جدول lookup_item...")
            
            # Create the table
            db.create_all()
            
            print("✅ جدول lookup_item ایجاد شد")
            
            # Add some sample data
            sample_data = [
                LookupItem(group='department', key='it', label='فناوری اطلاعات', order=1),
                LookupItem(group='department', key='hr', label='منابع انسانی', order=2),
                LookupItem(group='department', key='finance', label='مالی', order=3),
                LookupItem(group='office', key='tehran', label='تهران', order=1),
                LookupItem(group='office', key='mashhad', label='مشهد', order=2),
                LookupItem(group='vendor', key='microsoft', label='مایکروسافت', order=1),
                LookupItem(group='vendor', key='oracle', label='اوراکل', order=2),
            ]
            
            # Check if data already exists
            existing_count = LookupItem.query.count()
            if existing_count == 0:
                print("📝 افزودن داده‌های نمونه...")
                for item in sample_data:
                    db.session.add(item)
                db.session.commit()
                print(f"✅ {len(sample_data)} آیتم نمونه اضافه شد")
            else:
                print(f"ℹ️ {existing_count} آیتم موجود است - داده‌های نمونه اضافه نشد")
            
            print("✅ عملیات با موفقیت تکمیل شد!")
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در ایجاد جدول lookup_item: {e}")
            return False

if __name__ == '__main__':
    print("🚀 شروع ایجاد مجدد جدول lookup_item...")
    success = recreate_lookup_table()
    if success:
        print("✅ عملیات با موفقیت تکمیل شد!")
    else:
        print("❌ عملیات ناموفق بود!")
