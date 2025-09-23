"""
سرویس FreeIPA برای Flask CMS
"""

import os
from ldap3 import Server, Connection, ALL, SUBTREE
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class FreeIPAService:
    """سرویس FreeIPA برای احراز هویت و مدیریت کاربران"""
    
    def __init__(self):
        self.host = '192.168.0.34'
        self.port = 389
        self.use_ssl = False
        self.base_dn = 'dc=mci,dc=local'
        self.bind_dn = 'uid=admin,cn=users,cn=accounts,dc=mci,dc=local'
        self.bind_password = 'MyIPAAdminPass123!'
    
    def _get_config(self):
        """دریافت تنظیمات از Flask app"""
        try:
            return {
                'host': current_app.config.get('FREEIPA_HOST', self.host),
                'port': current_app.config.get('FREEIPA_PORT', self.port),
                'use_ssl': current_app.config.get('FREEIPA_USE_SSL', self.use_ssl),
                'base_dn': current_app.config.get('FREEIPA_BASE_DN', self.base_dn),
                'bind_dn': current_app.config.get('FREEIPA_BIND_DN', self.bind_dn),
                'bind_password': current_app.config.get('FREEIPA_BIND_PASSWORD', self.bind_password)
            }
        except:
            return {
                'host': self.host,
                'port': self.port,
                'use_ssl': self.use_ssl,
                'base_dn': self.base_dn,
                'bind_dn': self.bind_dn,
                'bind_password': self.bind_password
            }
        
    def _get_connection(self):
        """ایجاد اتصال به FreeIPA"""
        try:
            config = self._get_config()
            server = Server(config['host'], port=config['port'], use_ssl=config['use_ssl'], get_info=ALL)
            conn = Connection(server, user=config['bind_dn'], password=config['bind_password'])
            return conn
        except Exception as e:
            logger.error(f"خطا در ایجاد اتصال FreeIPA: {e}")
            return None
    
    def authenticate_user(self, username, password):
        """احراز هویت کاربر"""
        try:
            config = self._get_config()
            # اتصال برای bind (مسیر صحیح FreeIPA)
            bind_dn = f"uid={username},cn=users,cn=accounts,{config['base_dn']}"
            server = Server(config['host'], port=config['port'], use_ssl=config['use_ssl'])
            conn = Connection(server, user=bind_dn, password=password)
            
            if conn.bind():
                # دریافت اطلاعات کاربر
                user_info = self.get_user_info(username)
                conn.unbind()
                return True, user_info
            else:
                conn.unbind()
                return False, None
            
        except Exception as e:
            logger.error(f"خطا در احراز هویت کاربر {username}: {e}")
            return False, None
    
    def get_user_info(self, username):
        """دریافت اطلاعات کاربر"""
        try:
            conn = self._get_connection()
            if not conn:
                return None
                
            if conn.bind():
                config = self._get_config()
                search_filter = f"(uid={username})"
                conn.search(config['base_dn'], search_filter, SUBTREE, 
                           attributes=['cn', 'uid', 'mail', 'memberOf', 'givenName', 'sn'])
                
                if conn.entries:
                    user = conn.entries[0]
                    user_info = {
                        'username': str(user.uid),
                        'full_name': str(user.cn),
                        'email': str(user.mail) if hasattr(user, 'mail') else '',
                        'first_name': str(user.givenName) if hasattr(user, 'givenName') else '',
                        'last_name': str(user.sn) if hasattr(user, 'sn') else '',
                        'groups': [str(group) for group in user.memberOf] if hasattr(user, 'memberOf') else []
                    }
                    conn.unbind()
                    return user_info
                
                conn.unbind()
                return None
            else:
                conn.unbind()
                return None
            
        except Exception as e:
            logger.error(f"خطا در دریافت اطلاعات کاربر {username}: {e}")
            return None
    
    def get_all_users(self):
        """دریافت لیست تمام کاربران"""
        try:
            conn = self._get_connection()
            if not conn:
                return []
                
            if conn.bind():
                config = self._get_config()
                search_filter = "(objectClass=person)"
                conn.search(config['base_dn'], search_filter, SUBTREE,
                           attributes=['cn', 'uid', 'mail', 'memberOf'])
                
                users = []
                for entry in conn.entries:
                    user_info = {
                        'username': str(entry.uid),
                        'full_name': str(entry.cn),
                        'email': str(entry.mail) if hasattr(entry, 'mail') else '',
                        'groups': [str(group) for group in entry.memberOf] if hasattr(entry, 'memberOf') else []
                    }
                    users.append(user_info)
                
                conn.unbind()
                return users
            else:
                conn.unbind()
                return []
                
        except Exception as e:
            logger.error(f"خطا در دریافت لیست کاربران: {e}")
            return []
    
    def get_user_groups(self, username):
        """دریافت گروه‌های کاربر"""
        user_info = self.get_user_info(username)
        if user_info:
            return user_info.get('groups', [])
            return []
    
    def is_user_in_group(self, username, group_name):
        """بررسی عضویت کاربر در گروه"""
        groups = self.get_user_groups(username)
        return any(group_name in group for group in groups)
    
    def get_all_groups(self):
        """دریافت همه گروه‌های FreeIPA"""
        try:
            conn = self._get_connection()
            if not conn:
                return []
            if conn.bind():
                config = self._get_config()
                base_groups = f"cn=groups,cn=accounts,{config['base_dn']}"
                search_filter = "(objectClass=groupOfNames)"
                conn.search(base_groups, search_filter, SUBTREE,
                           attributes=['cn', 'description', 'gidNumber', 'member'])
                groups = []
                for entry in conn.entries:
                    groups.append({
                        'cn': str(getattr(entry, 'cn', '')),
                        'description': str(getattr(entry, 'description', '')) if hasattr(entry, 'description') else '',
                        'gid_number': str(getattr(entry, 'gidNumber', '')) if hasattr(entry, 'gidNumber') else '',
                        'members': list(entry.member) if hasattr(entry, 'member') else []
                    })
                conn.unbind()
                return groups
            else:
                conn.unbind()
                return []
        except Exception as e:
            logger.error(f"خطا در دریافت گروه‌ها: {e}")
            return []
    
    def test_connection(self):
        """تست اتصال به FreeIPA"""
        try:
            conn = self._get_connection()
            if conn and conn.bind():
                conn.unbind()
                return True, "اتصال موفق"
            else:
                return False, "اتصال ناموفق"
        except Exception as e:
            return False, f"خطا: {e}"

# ایجاد instance سراسری
try:
    # تلاش برای اتصال به FreeIPA واقعی
    test_service = FreeIPAService()
    success, _ = test_service.test_connection()
    if success:
        freeipa_service = test_service
    else:
        # استفاده از Mock در صورت عدم اتصال
        from freeipa_mock import freeipa_mock_service
        freeipa_service = freeipa_mock_service
except:
    # استفاده از Mock در صورت خطا
    from freeipa_mock import freeipa_mock_service
    freeipa_service = freeipa_mock_service