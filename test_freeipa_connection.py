#!/usr/bin/env python3
"""
اسکریپت تست اتصال به FreeIPA
"""

import os
import sys
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv('freeipa_config.env')

try:
    from ldap3 import Server, Connection, ALL
    print("✅ کتابخانه ldap3 نصب شده است")
except ImportError:
    print("❌ کتابخانه ldap3 نصب نشده است")
    print("برای نصب: pip install ldap3")
    sys.exit(1)

def test_freeipa_connection():
    """تست اتصال به FreeIPA"""
    
    # تنظیمات اتصال
    host = os.environ.get('FREEIPA_HOST', '192.168.0.36')
    port = int(os.environ.get('FREEIPA_PORT', 389))
    use_ssl = os.environ.get('FREEIPA_USE_SSL', 'false').lower() in ['true', 'on', '1']
    base_dn = os.environ.get('FREEIPA_BASE_DN', 'dc=mci,dc=local')
    bind_dn = os.environ.get('FREEIPA_BIND_DN', 'cn=mci,cn=users,dc=mci,dc=local')
    bind_password = os.environ.get('FREEIPA_BIND_PASSWORD', '')
    
    print(f"🔗 تست اتصال به FreeIPA...")
    print(f"   Host: {host}:{port}")
    print(f"   SSL: {use_ssl}")
    print(f"   Base DN: {base_dn}")
    print(f"   Bind DN: {bind_dn}")
    
    try:
        # ایجاد سرور
        server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL)
        print("✅ سرور FreeIPA ایجاد شد")
        
        # اتصال
        conn = Connection(server, user=bind_dn, password=bind_password)
        print("✅ اتصال به FreeIPA برقرار شد")
        
        # تست bind
        if conn.bind():
            print("✅ احراز هویت موفق")
            
            # جستجوی کاربران
            conn.search(base_dn, '(objectClass=person)', attributes=['cn', 'uid', 'mail'])
            print(f"✅ {len(conn.entries)} کاربر یافت شد")
            
            # نمایش کاربران
            for entry in conn.entries:
                print(f"   👤 {entry.cn} ({entry.uid}) - {entry.mail}")
            
            conn.unbind()
            print("✅ اتصال بسته شد")
            return True
            
        else:
            print("❌ احراز هویت ناموفق")
            print(f"   کد خطا: {conn.last_error}")
            return False
            
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False

def test_freeipa_users():
    """تست لیست کاربران FreeIPA"""
    
    host = os.environ.get('FREEIPA_HOST', '192.168.0.36')
    port = int(os.environ.get('FREEIPA_PORT', 389))
    use_ssl = os.environ.get('FREEIPA_USE_SSL', 'false').lower() in ['true', 'on', '1']
    base_dn = os.environ.get('FREEIPA_BASE_DN', 'dc=mci,dc=local')
    bind_dn = os.environ.get('FREEIPA_BIND_DN', 'cn=mci,cn=users,dc=mci,dc=local')
    bind_password = os.environ.get('FREEIPA_BIND_PASSWORD', '')
    
    try:
        server = Server(host, port=port, use_ssl=use_ssl)
        conn = Connection(server, user=bind_dn, password=bind_password)
        
        if conn.bind():
            # جستجوی کاربران
            conn.search(base_dn, '(objectClass=person)', attributes=['cn', 'uid', 'mail', 'memberOf'])
            
            print(f"\n📋 لیست کاربران FreeIPA:")
            for entry in conn.entries:
                print(f"   👤 {entry.cn} ({entry.uid})")
                if hasattr(entry, 'mail') and entry.mail:
                    print(f"      📧 {entry.mail}")
                if hasattr(entry, 'memberOf') and entry.memberOf:
                    print(f"      👥 گروه‌ها: {', '.join(entry.memberOf)}")
                print()
            
            conn.unbind()
            return True
        else:
            print("❌ احراز هویت ناموفق")
            return False
            
    except Exception as e:
        print(f"❌ خطا در دریافت لیست کاربران: {e}")
        return False

if __name__ == "__main__":
    print("=== تست اتصال FreeIPA ===\n")
    
    # تست اتصال
    if test_freeipa_connection():
        print("\n=== تست لیست کاربران ===\n")
        test_freeipa_users()
    
    print("\n✅ تست تکمیل شد!")