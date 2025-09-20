# FreeIPA Management Service
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from freeipa_client import FreeIPAClient
from sms_service import SMSService, PasswordManager
from models import (
    FreeIPAServer, FreeIPAUser, FreeIPAGroup, FreeIPAUserGroup, 
    UserPassword, SMSTemplate, SMSLog
)
from datetime import datetime, timedelta
import logging
import json
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class FreeIPAManager:
    """مدیریت کامل FreeIPA"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.sms_service = None
        self._init_sms_service()
    
    def _init_sms_service(self):
        """مقداردهی سرویس پیامک"""
        try:
            # دریافت تنظیمات از config
            sms_provider = current_app.config.get('SMS_PROVIDER', 'kavenegar')
            sms_api_key = current_app.config.get('SMS_API_KEY')
            sms_sender = current_app.config.get('SMS_SENDER')
            
            if sms_api_key:
                self.sms_service = SMSService(
                    provider=sms_provider,
                    api_key=sms_api_key,
                    sender=sms_sender
                )
        except Exception as e:
            logger.error(f"Failed to initialize SMS service: {e}")
    
    def get_active_server(self) -> Optional[FreeIPAServer]:
        """دریافت سرور فعال FreeIPA"""
        return self.db.query(FreeIPAServer).filter_by(is_active=True).first()
    
    def create_client(self, server: FreeIPAServer = None) -> Optional[FreeIPAClient]:
        """ایجاد کلاینت FreeIPA"""
        if not server:
            server = self.get_active_server()
        
        if not server:
            logger.error("No active FreeIPA server found")
            return None
        
        try:
            client = FreeIPAClient(
                hostname=server.hostname,
                port=server.port,
                use_ssl=server.use_ssl,
                base_dn=server.base_dn,
                bind_dn=server.bind_dn,
                bind_password=server.bind_password  # باید رمزگشایی شود
            )
            return client
        except Exception as e:
            logger.error(f"Failed to create FreeIPA client: {e}")
            return None
    
    def test_connection(self, server_id: int = None) -> Tuple[bool, str]:
        """تست اتصال به سرور FreeIPA"""
        try:
            if server_id:
                server = self.db.query(FreeIPAServer).get(server_id)
            else:
                server = self.get_active_server()
            
            if not server:
                return False, "No server found"
            
            client = self.create_client(server)
            if not client:
                return False, "Failed to create client"
            
            success, message = client.test_connection()
            
            # به‌روزرسانی وضعیت اتصال
            server.last_connection_test = datetime.utcnow()
            server.connection_status = 'connected' if success else 'failed'
            self.db.commit()
            
            return success, message
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e)
    
    def create_user(self, uid: str, cn: str, sn: str, givenname: str, 
                   mail: str, mobile: str = None, groups: List[str] = None,
                   send_sms: bool = True) -> Tuple[bool, str, str]:
        """ایجاد کاربر جدید در FreeIPA"""
        try:
            client = self.create_client()
            if not client:
                return False, "Failed to create FreeIPA client", ""
            
            # تولید پسورد
            password = PasswordManager.generate_secure_password()
            
            # ایجاد کاربر در FreeIPA
            success, message = client.create_user(
                uid=uid, cn=cn, sn=sn, givenname=givenname,
                mail=mail, mobile=mobile, password=password
            )
            
            if not success:
                return False, message, ""
            
            # ذخیره در پایگاه داده محلی
            freeipa_user = FreeIPAUser(
                uid=uid, cn=cn, sn=sn, givenname=givenname,
                mail=mail, mobile=mobile
            )
            self.db.add(freeipa_user)
            self.db.flush()  # برای دریافت ID
            
            # ذخیره پسورد
            user_password = UserPassword(
                user_id=freeipa_user.id,
                password_type='initial',
                expires_at=datetime.utcnow() + timedelta(days=7)  # انقضا در 7 روز
            )
            user_password.set_password(password)
            self.db.add(user_password)
            
            # اضافه کردن به گروه‌ها
            if groups:
                for group_cn in groups:
                    self.add_user_to_group(freeipa_user.id, group_cn)
            
            self.db.commit()
            
            # ارسال پیامک
            if send_sms and mobile and self.sms_service:
                self.send_password_sms(freeipa_user.id, password)
            
            logger.info(f"User {uid} created successfully")
            return True, "User created successfully", password
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create user {uid}: {e}")
            return False, str(e), ""
    
    def update_user(self, user_id: int, **kwargs) -> Tuple[bool, str]:
        """ویرایش کاربر"""
        try:
            freeipa_user = self.db.query(FreeIPAUser).get(user_id)
            if not freeipa_user:
                return False, "User not found"
            
            client = self.create_client()
            if not client:
                return False, "Failed to create FreeIPA client"
            
            # به‌روزرسانی در FreeIPA
            success, message = client.update_user(freeipa_user.uid, **kwargs)
            if not success:
                return False, message
            
            # به‌روزرسانی در پایگاه داده محلی
            for key, value in kwargs.items():
                if hasattr(freeipa_user, key) and value is not None:
                    setattr(freeipa_user, key, value)
            
            freeipa_user.updated_at = datetime.utcnow()
            self.db.commit()
            
            return True, "User updated successfully"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            return False, str(e)
    
    def change_password(self, user_id: int, new_password: str = None, 
                       send_sms: bool = True) -> Tuple[bool, str, str]:
        """تغییر پسورد کاربر"""
        try:
            freeipa_user = self.db.query(FreeIPAUser).get(user_id)
            if not freeipa_user:
                return False, "User not found", ""
            
            client = self.create_client()
            if not client:
                return False, "Failed to create FreeIPA client", ""
            
            # تولید پسورد جدید اگر ارائه نشده
            if not new_password:
                new_password = PasswordManager.generate_secure_password()
            
            # تغییر پسورد در FreeIPA
            success, message = client.update_user(freeipa_user.uid, password=new_password)
            if not success:
                return False, message, ""
            
            # ذخیره پسورد جدید
            user_password = UserPassword(
                user_id=freeipa_user.id,
                password_type='reset',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            user_password.set_password(new_password)
            self.db.add(user_password)
            
            self.db.commit()
            
            # ارسال پیامک
            if send_sms and freeipa_user.mobile and self.sms_service:
                self.send_password_sms(freeipa_user.id, new_password)
            
            return True, "Password changed successfully", new_password
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to change password for user {user_id}: {e}")
            return False, str(e), ""
    
    def add_user_to_group(self, user_id: int, group_cn: str) -> Tuple[bool, str]:
        """اضافه کردن کاربر به گروه"""
        try:
            freeipa_user = self.db.query(FreeIPAUser).get(user_id)
            if not freeipa_user:
                return False, "User not found"
            
            # بررسی وجود گروه در پایگاه داده محلی
            freeipa_group = self.db.query(FreeIPAGroup).filter_by(cn=group_cn).first()
            if not freeipa_group:
                # ایجاد گروه در FreeIPA و پایگاه داده
                success, message = self.create_group(group_cn)
                if not success:
                    return False, message
                freeipa_group = self.db.query(FreeIPAGroup).filter_by(cn=group_cn).first()
            
            client = self.create_client()
            if not client:
                return False, "Failed to create FreeIPA client"
            
            # اضافه کردن به گروه در FreeIPA
            success, message = client.add_user_to_group(freeipa_user.uid, group_cn)
            if not success:
                return False, message
            
            # اضافه کردن به گروه در پایگاه داده محلی
            user_group = FreeIPAUserGroup(
                user_id=user_id,
                group_id=freeipa_group.id
            )
            self.db.add(user_group)
            self.db.commit()
            
            return True, "User added to group successfully"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add user to group: {e}")
            return False, str(e)
    
    def remove_user_from_group(self, user_id: int, group_cn: str) -> Tuple[bool, str]:
        """حذف کاربر از گروه"""
        try:
            freeipa_user = self.db.query(FreeIPAUser).get(user_id)
            if not freeipa_user:
                return False, "User not found"
            
            client = self.create_client()
            if not client:
                return False, "Failed to create FreeIPA client"
            
            # حذف از گروه در FreeIPA
            success, message = client.remove_user_from_group(freeipa_user.uid, group_cn)
            if not success:
                return False, message
            
            # حذف از گروه در پایگاه داده محلی
            freeipa_group = self.db.query(FreeIPAGroup).filter_by(cn=group_cn).first()
            if freeipa_group:
                user_group = self.db.query(FreeIPAUserGroup).filter_by(
                    user_id=user_id, group_id=freeipa_group.id
                ).first()
                if user_group:
                    self.db.delete(user_group)
                    self.db.commit()
            
            return True, "User removed from group successfully"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove user from group: {e}")
            return False, str(e)
    
    def create_group(self, cn: str, description: str = None) -> Tuple[bool, str]:
        """ایجاد گروه"""
        try:
            client = self.create_client()
            if not client:
                return False, "Failed to create FreeIPA client"
            
            # ایجاد گروه در FreeIPA
            success, message = client.create_group(cn, description)
            if not success:
                return False, message
            
            # ذخیره در پایگاه داده محلی
            freeipa_group = FreeIPAGroup(cn=cn, description=description)
            self.db.add(freeipa_group)
            self.db.commit()
            
            return True, "Group created successfully"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create group {cn}: {e}")
            return False, str(e)
    
    def sync_users_from_freeipa(self) -> Tuple[bool, str]:
        """همگام‌سازی کاربران از FreeIPA"""
        try:
            client = self.create_client()
            if not client:
                return False, "Failed to create FreeIPA client"
            
            # دریافت لیست کاربران از FreeIPA
            users = client.list_users()
            
            for user_data in users:
                # بررسی وجود کاربر در پایگاه داده محلی
                existing_user = self.db.query(FreeIPAUser).filter_by(uid=user_data['uid']).first()
                
                if existing_user:
                    # به‌روزرسانی اطلاعات موجود
                    for key, value in user_data.items():
                        if hasattr(existing_user, key) and value:
                            setattr(existing_user, key, value)
                    existing_user.last_sync = datetime.utcnow()
                else:
                    # ایجاد کاربر جدید
                    new_user = FreeIPAUser(
                        uid=user_data['uid'],
                        cn=user_data['cn'],
                        sn=user_data['sn'],
                        givenname=user_data['givenName'],
                        mail=user_data['mail'],
                        mobile=user_data.get('mobile'),
                        last_sync=datetime.utcnow()
                    )
                    self.db.add(new_user)
            
            self.db.commit()
            return True, f"Synced {len(users)} users successfully"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to sync users: {e}")
            return False, str(e)
    
    def send_password_sms(self, user_id: int, password: str) -> Tuple[bool, str]:
        """ارسال پسورد از طریق پیامک"""
        try:
            freeipa_user = self.db.query(FreeIPAUser).get(user_id)
            if not freeipa_user or not freeipa_user.mobile:
                return False, "User not found or no mobile number"
            
            if not self.sms_service:
                return False, "SMS service not configured"
            
            # دریافت قالب پیامک
            template = self.db.query(SMSTemplate).filter_by(
                name='password_notification', is_active=True
            ).first()
            
            if template:
                message = template.template.format(
                    username=freeipa_user.uid,
                    password=password,
                    fullname=freeipa_user.cn
                )
            else:
                # قالب پیش‌فرض
                message = f"کاربر گرامی {freeipa_user.cn}، نام کاربری: {freeipa_user.uid}، رمز عبور: {password}"
            
            # ارسال پیامک
            result = self.sms_service.send_sms(freeipa_user.mobile, message)
            
            # ذخیره لاگ
            sms_log = SMSLog(
                user_id=user_id,
                phone_number=freeipa_user.mobile,
                message=message,
                template_id=template.id if template else None,
                provider=self.sms_service.provider,
                status='sent' if result['success'] else 'failed',
                message_id=result.get('message_id'),
                error_message=result.get('error'),
                cost=result.get('cost'),
                sent_at=datetime.utcnow() if result['success'] else None
            )
            self.db.add(sms_log)
            
            # به‌روزرسانی وضعیت ارسال پسورد
            if result['success']:
                user_password = self.db.query(UserPassword).filter_by(
                    user_id=user_id, is_sent=False
                ).order_by(UserPassword.created_at.desc()).first()
                
                if user_password:
                    user_password.is_sent = True
                    user_password.sent_at = datetime.utcnow()
            
            self.db.commit()
            
            if result['success']:
                return True, "SMS sent successfully"
            else:
                return False, result.get('error', 'SMS sending failed')
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to send SMS: {e}")
            return False, str(e)
    
    def get_user_passwords(self, user_id: int) -> List[Dict]:
        """دریافت پسوردهای کاربر"""
        try:
            passwords = self.db.query(UserPassword).filter_by(user_id=user_id).order_by(
                UserPassword.created_at.desc()
            ).all()
            
            result = []
            for pwd in passwords:
                result.append({
                    'id': pwd.id,
                    'type': pwd.password_type,
                    'is_sent': pwd.is_sent,
                    'sent_at': pwd.sent_at,
                    'expires_at': pwd.expires_at,
                    'is_expired': pwd.is_expired(),
                    'created_at': pwd.created_at,
                    'creator': pwd.creator.username if pwd.creator else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user passwords: {e}")
            return []
    
    def resend_password_sms(self, password_id: int) -> Tuple[bool, str]:
        """ارسال مجدد پیامک پسورد"""
        try:
            user_password = self.db.query(UserPassword).get(password_id)
            if not user_password:
                return False, "Password record not found"
            
            if user_password.is_expired():
                return False, "Password has expired"
            
            # دریافت پسورد اصلی (نیاز به رمزگشایی)
            # در اینجا باید پسورد را از FreeIPA دریافت کنیم
            freeipa_user = user_password.user
            client = self.create_client()
            
            if not client:
                return False, "Failed to create FreeIPA client"
            
            # دریافت اطلاعات کاربر از FreeIPA
            user_info = client.get_user(freeipa_user.uid)
            if not user_info:
                return False, "User not found in FreeIPA"
            
            # ارسال پیامک با پسورد فعلی
            return self.send_password_sms(freeipa_user.id, "***")  # پسورد نمایش داده نمی‌شود
            
        except Exception as e:
            logger.error(f"Failed to resend password SMS: {e}")
            return False, str(e)
