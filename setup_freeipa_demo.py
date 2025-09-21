#!/usr/bin/env python3
"""
اسکریپت راه‌اندازی FreeIPA برای تست
"""

import subprocess
import time
import requests
import json
from freeipa_service import FreeIPAManager
from models import db, FreeIPAServer, User
from app import app

def check_docker():
    """بررسی نصب Docker"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker نصب است")
            return True
        else:
            print("❌ Docker نصب نیست")
            return False
    except FileNotFoundError:
        print("❌ Docker نصب نیست")
        return False

def start_freeipa():
    """راه‌اندازی FreeIPA با Docker"""
    print("🚀 راه‌اندازی FreeIPA...")
    
    try:
        # توقف کانتینرهای موجود
        subprocess.run(['docker', 'stop', 'freeipa-server'], capture_output=True)
        subprocess.run(['docker', 'rm', 'freeipa-server'], capture_output=True)
        
        # راه‌اندازی FreeIPA
        cmd = [
            'docker', 'run', '-d',
            '--name', 'freeipa-server',
            '--hostname', 'ipa.example.com',
            '-p', '80:80',
            '-p', '443:443', 
            '-p', '389:389',
            '-p', '636:636',
            '-e', 'IPA_SERVER_IP=127.0.0.1',
            '-e', 'PASSWORD=MySecretPassword123',
            '--sysctl', 'net.ipv6.conf.all.disable_ipv6=0',
            '--privileged',
            'freeipa/freeipa-server:latest'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FreeIPA راه‌اندازی شد")
            return True
        else:
            print(f"❌ خطا در راه‌اندازی FreeIPA: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی FreeIPA: {e}")
        return False

def wait_for_freeipa():
    """انتظار برای آماده شدن FreeIPA"""
    print("⏳ انتظار برای آماده شدن FreeIPA...")
    
    for i in range(60):  # 5 دقیقه انتظار
        try:
            response = requests.get('http://localhost', timeout=5)
            if response.status_code == 200:
                print("✅ FreeIPA آماده است")
                return True
        except:
            pass
        
        print(f"⏳ {i+1}/60 - انتظار...")
        time.sleep(5)
    
    print("❌ FreeIPA در زمان مقرر آماده نشد")
    return False

def setup_freeipa_server():
    """تنظیم سرور FreeIPA در دیتابیس"""
    print("🔧 تنظیم سرور FreeIPA در دیتابیس...")
    
    with app.app_context():
        # حذف سرورهای موجود
        FreeIPAServer.query.delete()
        
        # ایجاد سرور جدید
        server = FreeIPAServer(
            name='FreeIPA Demo Server',
            hostname='127.0.0.1',
            port=389,
            use_ssl=False,
            base_dn='dc=example,dc=com',
            bind_dn='cn=admin,cn=users,dc=example,dc=com',
            bind_password='MySecretPassword123',
            is_active=True
        )
        
        db.session.add(server)
        db.session.commit()
        
        print("✅ سرور FreeIPA در دیتابیس تنظیم شد")
        return server.id

def test_connection(server_id):
    """تست اتصال به FreeIPA"""
    print("🔍 تست اتصال به FreeIPA...")
    
    with app.app_context():
        manager = FreeIPAManager()
        success, message = manager.test_connection(server_id)
        
        if success:
            print(f"✅ اتصال موفق: {message}")
            return True
        else:
            print(f"❌ اتصال ناموفق: {message}")
            return False

def create_demo_users(server_id):
    """ایجاد کاربران نمونه"""
    print("👥 ایجاد کاربران نمونه...")
    
    with app.app_context():
        manager = FreeIPAManager()
        
        demo_users = [
            {
                'uid': 'john.doe',
                'cn': 'John Doe',
                'sn': 'Doe',
                'givenname': 'John',
                'mail': 'john.doe@example.com',
                'mobile': '09123456789'
            },
            {
                'uid': 'jane.smith',
                'cn': 'Jane Smith', 
                'sn': 'Smith',
                'givenname': 'Jane',
                'mail': 'jane.smith@example.com',
                'mobile': '09123456790'
            }
        ]
        
        for user_data in demo_users:
            try:
                success, message = manager.create_user(server_id, user_data)
                if success:
                    print(f"✅ کاربر {user_data['uid']} ایجاد شد")
                else:
                    print(f"❌ خطا در ایجاد کاربر {user_data['uid']}: {message}")
            except Exception as e:
                print(f"❌ خطا در ایجاد کاربر {user_data['uid']}: {e}")

def main():
    """تابع اصلی"""
    print("🎯 راه‌اندازی FreeIPA برای تست عملیاتی")
    print("=" * 50)
    
    # بررسی Docker
    if not check_docker():
        print("لطفاً Docker را نصب کنید")
        return
    
    # راه‌اندازی FreeIPA
    if not start_freeipa():
        return
    
    # انتظار برای آماده شدن
    if not wait_for_freeipa():
        return
    
    # تنظیم سرور در دیتابیس
    server_id = setup_freeipa_server()
    
    # تست اتصال
    if not test_connection(server_id):
        print("⚠️ اتصال برقرار نشد، اما سرور تنظیم شد")
    
    # ایجاد کاربران نمونه
    create_demo_users(server_id)
    
    print("\n🎉 راه‌اندازی تکمیل شد!")
    print("🌐 FreeIPA Web UI: http://localhost")
    print("🔐 Admin: admin / MySecretPassword123")
    print("📱 Flask CMS: http://localhost:5000")

if __name__ == "__main__":
    main()




