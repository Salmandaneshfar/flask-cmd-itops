#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت تست عملکرد اضافه کردن lookup
"""

from app import create_app
from models import db, LookupItem

def test_lookup_add():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 تست عملکرد اضافه کردن lookup...")
            
            # Check existing count
            existing_count = LookupItem.query.count()
            print(f"📊 تعداد آیتم‌های موجود: {existing_count}")
            
            # Test creating a new lookup item
            test_item = LookupItem(
                group='test',
                key='test_key',
                label='Test Label',
                order=999,
                is_active=True
            )
            
            print("📝 ایجاد آیتم تست...")
            db.session.add(test_item)
            db.session.commit()
            
            print(f"✅ آیتم تست با موفقیت اضافه شد: ID={test_item.id}")
            
            # Verify it was added
            new_count = LookupItem.query.count()
            print(f"📊 تعداد آیتم‌ها بعد از اضافه کردن: {new_count}")
            
            # Clean up - remove test item
            db.session.delete(test_item)
            db.session.commit()
            print("🧹 آیتم تست حذف شد")
            
            final_count = LookupItem.query.count()
            print(f"📊 تعداد نهایی آیتم‌ها: {final_count}")
            
            print("✅ تست با موفقیت تکمیل شد!")
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در تست: {e}")
            return False

if __name__ == '__main__':
    print("🚀 شروع تست عملکرد اضافه کردن lookup...")
    success = test_lookup_add()
    if success:
        print("✅ همه تست‌ها موفق بود!")
    else:
        print("❌ تست ناموفق بود!")
