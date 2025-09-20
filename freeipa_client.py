# FreeIPA Client
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPSocketOpenError
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import secrets
import string

logger = logging.getLogger(__name__)

class FreeIPAClient:
    """کلاینت برای اتصال و مدیریت FreeIPA"""
    
    def __init__(self, hostname: str, port: int = 389, use_ssl: bool = True, 
                 base_dn: str = "", bind_dn: str = "", bind_password: str = ""):
        self.hostname = hostname
        self.port = port
        self.use_ssl = use_ssl
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.connection = None
        
    def connect(self) -> bool:
        """اتصال به سرور FreeIPA"""
        try:
            # ایجاد سرور
            server = Server(
                host=self.hostname,
                port=self.port,
                use_ssl=self.use_ssl,
                get_info=ALL
            )
            
            # ایجاد اتصال
            self.connection = Connection(
                server=server,
                user=self.bind_dn,
                password=self.bind_password,
                auto_bind=True
            )
            
            logger.info(f"Successfully connected to FreeIPA server: {self.hostname}")
            return True
            
        except (LDAPException, LDAPBindError, LDAPSocketOpenError) as e:
            logger.error(f"Failed to connect to FreeIPA: {e}")
            return False
    
    def disconnect(self):
        """قطع اتصال"""
        if self.connection:
            self.connection.unbind()
            self.connection = None
    
    def create_user(self, uid: str, cn: str, sn: str, givenname: str, 
                   mail: str, mobile: str = None, password: str = None) -> Tuple[bool, str]:
        """ایجاد کاربر جدید"""
        try:
            if not self.connection:
                if not self.connect():
                    return False, "Failed to connect to FreeIPA"
            
            # تولید پسورد اگر ارائه نشده
            if not password:
                password = self.generate_password()
            
            # DN برای کاربر
            user_dn = f"uid={uid},cn=users,cn=accounts,{self.base_dn}"
            
            # ویژگی‌های کاربر
            attrs = {
                'objectClass': ['top', 'person', 'organizationalPerson', 'inetOrgPerson', 'inetUser', 'posixAccount'],
                'uid': [uid],
                'cn': [cn],
                'sn': [sn],
                'givenName': [givenname],
                'mail': [mail],
                'userPassword': [password],
                'loginShell': ['/bin/bash'],
                'homeDirectory': [f'/home/{uid}'],
            }
            
            if mobile:
                attrs['mobile'] = [mobile]
            
            # ایجاد کاربر
            success = self.connection.add(user_dn, attributes=attrs)
            
            if success:
                logger.info(f"User {uid} created successfully")
                return True, password
            else:
                error_msg = self.connection.last_error
                if "already exists" in error_msg.lower():
                    return False, "User already exists"
                else:
                    return False, error_msg
            
        except LDAPException as e:
            logger.error(f"Failed to create user {uid}: {e}")
            return False, str(e)
    
    def update_user(self, uid: str, **kwargs) -> Tuple[bool, str]:
        """ویرایش کاربر"""
        try:
            if not self.connection:
                if not self.connect():
                    return False, "Failed to connect to FreeIPA"
            
            user_dn = f"uid={uid},cn=users,cn=accounts,{self.base_dn}"
            
            # آماده‌سازی تغییرات
            changes = {}
            for key, value in kwargs.items():
                if value is not None:
                    if key == 'password':
                        changes['userPassword'] = [(MODIFY_REPLACE, [value])]
                    elif key == 'mobile':
                        changes['mobile'] = [(MODIFY_REPLACE, [value])]
                    elif key == 'mail':
                        changes['mail'] = [(MODIFY_REPLACE, [value])]
                    elif key == 'cn':
                        changes['cn'] = [(MODIFY_REPLACE, [value])]
                    elif key == 'sn':
                        changes['sn'] = [(MODIFY_REPLACE, [value])]
                    elif key == 'givenname':
                        changes['givenName'] = [(MODIFY_REPLACE, [value])]
            
            if changes:
                success = self.connection.modify(user_dn, changes)
                if success:
                    logger.info(f"User {uid} updated successfully")
                    return True, "User updated successfully"
                else:
                    return False, self.connection.last_error
            else:
                return True, "No changes to update"
                
        except LDAPException as e:
            logger.error(f"Failed to update user {uid}: {e}")
            return False, str(e)
    
    def delete_user(self, uid: str) -> Tuple[bool, str]:
        """حذف کاربر"""
        try:
            if not self.connection:
                if not self.connect():
                    return False, "Failed to connect to FreeIPA"
            
            user_dn = f"uid={uid},cn=users,cn=accounts,{self.base_dn}"
            success = self.connection.delete(user_dn)
            
            if success:
                logger.info(f"User {uid} deleted successfully")
                return True, "User deleted successfully"
            else:
                return False, self.connection.last_error
            
        except LDAPException as e:
            logger.error(f"Failed to delete user {uid}: {e}")
            return False, str(e)
    
    def get_user(self, uid: str) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        try:
            if not self.connection:
                if not self.connect():
                    return None
            
            user_dn = f"uid={uid},cn=users,cn=accounts,{self.base_dn}"
            success = self.connection.search(
                search_base=user_dn,
                search_scope=SUBTREE,
                search_filter='(objectClass=*)',
                attributes=['*']
            )
            
            if success and self.connection.entries:
                entry = self.connection.entries[0]
                return {
                    'uid': str(entry.uid) if hasattr(entry, 'uid') else '',
                    'cn': str(entry.cn) if hasattr(entry, 'cn') else '',
                    'sn': str(entry.sn) if hasattr(entry, 'sn') else '',
                    'givenName': str(entry.givenName) if hasattr(entry, 'givenName') else '',
                    'mail': str(entry.mail) if hasattr(entry, 'mail') else '',
                    'mobile': str(entry.mobile) if hasattr(entry, 'mobile') else None,
                    'uidNumber': str(entry.uidNumber) if hasattr(entry, 'uidNumber') else None,
                    'gidNumber': str(entry.gidNumber) if hasattr(entry, 'gidNumber') else None,
                }
            return None
            
        except LDAPException as e:
            logger.error(f"Failed to get user {uid}: {e}")
            return None
    
    def list_users(self, limit: int = 100) -> List[Dict]:
        """لیست کاربران"""
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            search_base = f"cn=users,cn=accounts,{self.base_dn}"
            search_filter = "(objectClass=inetUser)"
            
            success = self.connection.search(
                search_base=search_base,
                search_scope=SUBTREE,
                search_filter=search_filter,
                attributes=['uid', 'cn', 'sn', 'givenName', 'mail', 'mobile']
            )
            
            users = []
            if success and self.connection.entries:
                for entry in self.connection.entries[:limit]:
                    users.append({
                        'uid': str(entry.uid) if hasattr(entry, 'uid') else '',
                        'cn': str(entry.cn) if hasattr(entry, 'cn') else '',
                        'sn': str(entry.sn) if hasattr(entry, 'sn') else '',
                        'givenName': str(entry.givenName) if hasattr(entry, 'givenName') else '',
                        'mail': str(entry.mail) if hasattr(entry, 'mail') else '',
                        'mobile': str(entry.mobile) if hasattr(entry, 'mobile') else None,
                    })
            
            return users
            
        except LDAPException as e:
            logger.error(f"Failed to list users: {e}")
            return []
    
    def create_group(self, cn: str, description: str = None) -> Tuple[bool, str]:
        """ایجاد گروه"""
        try:
            if not self.connection:
                if not self.connect():
                    return False, "Failed to connect to FreeIPA"
            
            group_dn = f"cn={cn},cn=groups,cn=accounts,{self.base_dn}"
            
            attrs = {
                'objectClass': ['top', 'groupOfNames', 'posixGroup'],
                'cn': [cn],
            }
            
            if description:
                attrs['description'] = [description]
            
            success = self.connection.add(group_dn, attributes=attrs)
            
            if success:
                logger.info(f"Group {cn} created successfully")
                return True, "Group created successfully"
            else:
                if "already exists" in self.connection.last_error.lower():
                    return False, "Group already exists"
                else:
                    return False, self.connection.last_error
            
        except LDAPException as e:
            logger.error(f"Failed to create group {cn}: {e}")
            return False, str(e)
    
    def add_user_to_group(self, uid: str, group_cn: str) -> Tuple[bool, str]:
        """اضافه کردن کاربر به گروه"""
        try:
            if not self.connection:
                if not self.connect():
                    return False, "Failed to connect to FreeIPA"
            
            group_dn = f"cn={group_cn},cn=groups,cn=accounts,{self.base_dn}"
            user_dn = f"uid={uid},cn=users,cn=accounts,{self.base_dn}"
            
            # اضافه کردن کاربر به گروه
            changes = {
                'member': [(MODIFY_ADD, [user_dn])]
            }
            
            success = self.connection.modify(group_dn, changes)
            
            if success:
                logger.info(f"User {uid} added to group {group_cn}")
                return True, "User added to group successfully"
            else:
                if "already exists" in self.connection.last_error.lower():
                    return True, "User already in group"
                else:
                    return False, self.connection.last_error
            
        except LDAPException as e:
            logger.error(f"Failed to add user {uid} to group {group_cn}: {e}")
            return False, str(e)
    
    def remove_user_from_group(self, uid: str, group_cn: str) -> Tuple[bool, str]:
        """حذف کاربر از گروه"""
        try:
            if not self.connection:
                if not self.connect():
                    return False, "Failed to connect to FreeIPA"
            
            group_dn = f"cn={group_cn},cn=groups,cn=accounts,{self.base_dn}"
            user_dn = f"uid={uid},cn=users,cn=accounts,{self.base_dn}"
            
            # حذف کاربر از گروه
            changes = {
                'member': [(MODIFY_DELETE, [user_dn])]
            }
            
            success = self.connection.modify(group_dn, changes)
            
            if success:
                logger.info(f"User {uid} removed from group {group_cn}")
                return True, "User removed from group successfully"
            else:
                if "no such attribute" in self.connection.last_error.lower():
                    return True, "User not in group"
                else:
                    return False, self.connection.last_error
            
        except LDAPException as e:
            logger.error(f"Failed to remove user {uid} from group {group_cn}: {e}")
            return False, str(e)
    
    def generate_password(self, length: int = 12) -> str:
        """تولید پسورد امن"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def test_connection(self) -> Tuple[bool, str]:
        """تست اتصال"""
        try:
            if self.connect():
                self.disconnect()
                return True, "Connection successful"
            else:
                return False, "Connection failed"
        except Exception as e:
            return False, str(e)