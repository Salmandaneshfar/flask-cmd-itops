#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت تست کامل فرم lookup
"""

from app import create_app
from models import db, LookupItem

def test_lookup_form():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 تست کامل فرم lookup...")
            
            # Test 1: Check if we can access the add form
            with app.test_client() as client:
                print("📝 تست دسترسی به فرم اضافه کردن...")
                response = client.get('/lookups/add')
                print(f"Status Code: {response.status_code}")
                if response.status_code == 200:
                    print("✅ فرم اضافه کردن قابل دسترسی است")
                else:
                    print("❌ مشکل در دسترسی به فرم")
                    return False
            
            # Test 2: Check if we can access the main lookups page
            with app.test_client() as client:
                print("📝 تست دسترسی به صفحه اصلی lookups...")
                response = client.get('/lookups')
                print(f"Status Code: {response.status_code}")
                if response.status_code == 200:
                    print("✅ صفحه اصلی lookups قابل دسترسی است")
                else:
                    print("❌ مشکل در دسترسی به صفحه اصلی")
                    return False
            
            # Test 3: Check existing data
            existing_count = LookupItem.query.count()
            print(f"📊 تعداد آیتم‌های موجود: {existing_count}")
            
            # Test 4: Test creating a lookup item directly
            print("📝 تست ایجاد آیتم مستقیم...")
            test_item = LookupItem(
                group='test',
                key='test_key',
                label='Test Label',
                order=999,
                is_active=True
            )
            
            db.session.add(test_item)
            db.session.commit()
            print(f"✅ آیتم تست ایجاد شد: ID={test_item.id}")
            
            # Clean up
            db.session.delete(test_item)
            db.session.commit()
            print("🧹 آیتم تست حذف شد")
            
            print("✅ همه تست‌ها موفق بود!")
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در تست: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("🚀 شروع تست کامل فرم lookup...")
    success = test_lookup_form()
    if success:
        print("✅ همه تست‌ها موفق بود!")
    else:
        print("❌ تست ناموفق بود!")
