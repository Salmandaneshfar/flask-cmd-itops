#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت حذف جدول lookup_item از دیتابیس
"""

from app import create_app
from models import db
from sqlalchemy import text

def remove_lookup_table():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if we're using SQLite or PostgreSQL
            engine = db.get_engine()
            dialect = engine.dialect.name
            
            print(f"🔍 تشخیص نوع دیتابیس: {dialect}")
            
            # Check if lookup_item table exists
            if dialect == 'sqlite':
                result = db.engine.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='lookup_item'"))
                table_exists = result.fetchone() is not None
            else:
                result = db.engine.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'lookup_item'"))
                table_exists = result.fetchone() is not None
            
            if not table_exists:
                print("ℹ️ جدول lookup_item وجود ندارد - نیازی به حذف نیست")
                return True
            
            print("📝 حذف جدول lookup_item...")
            
            # Drop the table
            db.engine.execute(text("DROP TABLE IF EXISTS lookup_item"))
            
            print("✅ جدول lookup_item با موفقیت حذف شد")
            
            # Commit changes
            db.session.commit()
            print("✅ تغییرات با موفقیت اعمال شد")
            
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در حذف جدول lookup_item: {e}")
            return False

if __name__ == '__main__':
    print("🚀 شروع حذف جدول lookup_item...")
    success = remove_lookup_table()
    if success:
        print("✅ عملیات با موفقیت تکمیل شد!")
    else:
        print("❌ عملیات ناموفق بود!")
