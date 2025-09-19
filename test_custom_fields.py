from app import app, db
from models import CustomField, CustomFieldValue, User

def test_custom_fields():
    with app.app_context():
        # ایجاد یک فیلد تست
        test_field = CustomField(
            name='test_field',
            label='فیلد تست',
            field_type='text',
            model_name='User',
            is_active=True
        )
        db.session.add(test_field)
        db.session.commit()
        print(f"✅ فیلد تست ایجاد شد: ID={test_field.id}")
        
        # ایجاد یک کاربر تست
        test_user = User(
            username='test_user',
            email='test@example.com',
            role='user'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
        print(f"✅ کاربر تست ایجاد شد: ID={test_user.id}")
        
        # تست ذخیره مقدار
        field_value = CustomFieldValue(
            field_id=test_field.id,
            model_name='User',
            record_id=test_user.id,
            value='مقدار تست'
        )
        db.session.add(field_value)
        db.session.commit()
        print(f"✅ مقدار فیلد ذخیره شد: {field_value.value}")
        
        # تست خواندن مقدار
        saved_value = CustomFieldValue.query.filter_by(
            field_id=test_field.id,
            model_name='User',
            record_id=test_user.id
        ).first()
        
        if saved_value:
            print(f"✅ مقدار خوانده شد: {saved_value.value}")
        else:
            print("❌ مقدار خوانده نشد!")
        
        # تست به‌روزرسانی
        saved_value.value = 'مقدار جدید'
        db.session.commit()
        print(f"✅ مقدار به‌روزرسانی شد: {saved_value.value}")
        
        # تست حذف
        db.session.delete(saved_value)
        db.session.commit()
        print("✅ مقدار حذف شد")
        
        # پاک‌سازی
        db.session.delete(test_field)
        db.session.delete(test_user)
        db.session.commit()
        print("✅ داده‌های تست پاک شدند")

if __name__ == '__main__':
    test_custom_fields()
