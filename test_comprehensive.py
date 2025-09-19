#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت تست جامع سیستم فیلدهای داینامیک
"""

import requests
import json
import time

def test_api_endpoints():
    """تست API endpoints"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 شروع تست API endpoints...")
    
    # Test models
    test_models = ['User', 'Server', 'Task', 'Content', 'Backup']
    
    for model in test_models:
        try:
            print(f"\n📡 تست API برای مدل: {model}")
            response = requests.get(f"{base_url}/api/custom-fields/{model}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ موفق - {len(data)} فیلد یافت شد")
                
            else:
                print(f"   ❌ خطا - وضعیت: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ خطا در تست {model}: {e}")
    
    print("\n✅ تست API endpoints تکمیل شد")

def test_field_values():
    """تست ذخیره و بازیابی مقادیر فیلدها"""
    base_url = "http://127.0.0.1:5000"
    
    print("\n🧪 شروع تست ذخیره و بازیابی مقادیر...")
    
    # Test data
    test_data = {
        'field_id': 1,
        'model_name': 'User',
        'record_id': 1,
        'value': 'مقدار تست'
    }
    
    try:
        print("📤 ارسال داده برای ذخیره...")
        response = requests.post(
            f"{base_url}/api/custom-field-value",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ ذخیره موفق")
            else:
                print(f"   ❌ خطا در ذخیره: {result.get('error')}")
        else:
            print(f"   ❌ خطا - وضعیت: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ خطا در تست ذخیره: {e}")
    
    try:
        print("📥 بازیابی مقادیر...")
        response = requests.get(f"{base_url}/api/custom-field-values/User/1")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ بازیابی موفق - {len(data)} مقدار یافت شد")
            for field_name, field_data in data.items():
                print(f"      - {field_name}: {field_data['value']}")
        else:
            print(f"   ❌ خطا - وضعیت: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ خطا در تست بازیابی: {e}")
    
    print("\n✅ تست ذخیره و بازیابی تکمیل شد")

def test_web_pages():
    """تست صفحات وب"""
    base_url = "http://127.0.0.1:5000"
    
    print("\n🧪 شروع تست صفحات وب...")
    
    test_pages = [
        '/custom-fields',
        '/test-all-fields',
        '/test-dropdown'
    ]
    
    for page in test_pages:
        try:
            print(f"🌐 تست صفحه: {page}")
            response = requests.get(f"{base_url}{page}")
            
            if response.status_code == 200:
                print(f"   ✅ صفحه بارگذاری شد")
                
                # Check for specific content
                content = response.text
                if 'فیلدهای سفارشی' in content or 'تست' in content:
                    print(f"   ✅ محتوای فارسی یافت شد")
                else:
                    print(f"   ⚠️ محتوای فارسی یافت نشد")
                    
            else:
                print(f"   ❌ خطا - وضعیت: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ خطا در تست صفحه {page}: {e}")
    
    print("\n✅ تست صفحات وب تکمیل شد")

def main():
    print("🚀 شروع تست جامع سیستم فیلدهای داینامیک")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ انتظار برای آماده شدن سرور...")
    time.sleep(2)
    
    # Run tests
    test_api_endpoints()
    test_field_values()
    test_web_pages()
    
    print("\n" + "=" * 50)
    print("✅ تست جامع تکمیل شد!")
    print("\n🌐 برای تست دستی به آدرس زیر بروید:")
    print("   http://127.0.0.1:5000/test-all-fields")
    print("\n📋 چک‌لیست تست دستی:")
    print("   1. باز کردن صفحه تست")
    print("   2. تست API برای مدل‌های مختلف")
    print("   3. تست اعتبارسنجی فیلدها")
    print("   4. تست ذخیره مقادیر")
    print("   6. تست فیلدهای فارسی")

if __name__ == '__main__':
    main()
