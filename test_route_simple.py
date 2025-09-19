#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت تست ساده route ها
"""

from app import create_app
from models import db, LookupItem

def test_routes():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 تست route های lookup...")
            
            # Check if routes are registered
            with app.app_context():
                rules = []
                for rule in app.url_map.iter_rules():
                    if 'lookup' in rule.rule:
                        rules.append(rule.rule)
                
                print("📋 Route های lookup موجود:")
                for rule in rules:
                    print(f"  - {rule}")
                
                if not rules:
                    print("❌ هیچ route lookup یافت نشد!")
                    return False
                else:
                    print("✅ Route های lookup موجود هستند")
            
            # Test database operations
            print("📝 تست عملیات دیتابیس...")
            existing_count = LookupItem.query.count()
            print(f"📊 تعداد آیتم‌های موجود: {existing_count}")
            
            # Test creating a lookup item
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
    print("🚀 شروع تست route های lookup...")
    success = test_routes()
    if success:
        print("✅ همه تست‌ها موفق بود!")
    else:
        print("❌ تست ناموفق بود!")
