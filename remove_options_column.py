#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت حذف ستون options از جدول custom_field
"""

from app import create_app
from models import db
from sqlalchemy import text

def remove_options_column():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if we're using SQLite or PostgreSQL
            engine = db.get_engine()
            dialect = engine.dialect.name
            
            print(f"🔍 تشخیص نوع دیتابیس: {dialect}")
            
            if dialect == 'sqlite':
                # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
                print("📝 SQLite تشخیص داده شد - بازسازی جدول...")
                
                # Create new table without options column
                db.engine.execute(text("""
                    CREATE TABLE custom_field_new (
                        id INTEGER NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        label VARCHAR(200) NOT NULL,
                        field_type VARCHAR(50) NOT NULL,
                        model_name VARCHAR(50) NOT NULL,
                        is_required BOOLEAN DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1,
                        placeholder VARCHAR(200),
                        help_text TEXT,
                        "order" INTEGER DEFAULT 0,
                        created_at DATETIME,
                        updated_at DATETIME,
                        PRIMARY KEY (id)
                    )
                """))
                
                # Copy data from old table to new table (excluding options column)
                db.engine.execute(text("""
                    INSERT INTO custom_field_new 
                    (id, name, label, field_type, model_name, is_required, is_active, 
                     placeholder, help_text, "order", created_at, updated_at)
                    SELECT id, name, label, field_type, model_name, is_required, is_active,
                           placeholder, help_text, "order", created_at, updated_at
                    FROM custom_field
                """))
                
                # Drop old table
                db.engine.execute(text("DROP TABLE custom_field"))
                
                # Rename new table
                db.engine.execute(text("ALTER TABLE custom_field_new RENAME TO custom_field"))
                
                print("✅ جدول SQLite با موفقیت بازسازی شد")
                
            elif dialect == 'postgresql':
                # PostgreSQL supports DROP COLUMN
                print("📝 PostgreSQL تشخیص داده شد - حذف ستون...")
                
                db.engine.execute(text("ALTER TABLE custom_field DROP COLUMN IF EXISTS options"))
                
                print("✅ ستون options از PostgreSQL حذف شد")
                
            else:
                print(f"⚠️ نوع دیتابیس {dialect} پشتیبانی نمی‌شود")
                return False
            
            # Commit changes
            db.session.commit()
            print("✅ تغییرات با موفقیت اعمال شد")
            
            # Verify the change
            if dialect == 'sqlite':
                result = db.engine.execute(text("PRAGMA table_info(custom_field)"))
                columns = [row[1] for row in result]  # Column name is at index 1 in SQLite
            else:
                result = db.engine.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'custom_field'"))
                columns = [row[0] for row in result]
            print(f"📊 ستون‌های موجود: {', '.join(columns)}")
            
            if 'options' not in columns:
                print("✅ ستون options با موفقیت حذف شد")
                return True
            else:
                print("❌ ستون options هنوز موجود است")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در حذف ستون options: {e}")
            return False

if __name__ == '__main__':
    print("🚀 شروع حذف ستون options از جدول custom_field...")
    success = remove_options_column()
    if success:
        print("✅ عملیات با موفقیت تکمیل شد!")
    else:
        print("❌ عملیات ناموفق بود!")
