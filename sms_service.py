# SMS Service
import requests
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

class SMSService:
    """سرویس ارسال پیامک"""
    
    def __init__(self, provider: str = 'kavenegar', api_key: str = None, sender: str = None):
        self.provider = provider
        self.api_key = api_key
        self.sender = sender
        
    def send_sms(self, phone_number: str, message: str) -> Dict:
        """ارسال پیامک"""
        try:
            if self.provider == 'kavenegar':
                return self._send_kavenegar(phone_number, message)
            elif self.provider == 'melipayamak':
                return self._send_melipayamak(phone_number, message)
            elif self.provider == 'sms_ir':
                return self._send_sms_ir(phone_number, message)
            else:
                return {'success': False, 'error': 'Unsupported SMS provider'}
                
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_kavenegar(self, phone_number: str, message: str) -> Dict:
        """ارسال پیامک از طریق کاوه‌نگار"""
        try:
            url = "https://api.kavenegar.com/v1/{}/sms/send.json".format(self.api_key)
            
            data = {
                'receptor': phone_number,
                'message': message,
                'sender': self.sender
            }
            
            response = requests.post(url, data=data, timeout=30)
            result = response.json()
            
            if result.get('return', {}).get('status') == 200:
                return {
                    'success': True,
                    'message_id': result.get('entries', [{}])[0].get('messageid'),
                    'cost': result.get('entries', [{}])[0].get('cost'),
                    'provider_response': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('return', {}).get('message', 'Unknown error'),
                    'provider_response': result
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_melipayamak(self, phone_number: str, message: str) -> Dict:
        """ارسال پیامک از طریق ملی‌پیامک"""
        try:
            url = "https://rest.payamak-resan.com/api/SendSMS/SendSMS"
            
            data = {
                'username': self.api_key,
                'password': self.api_key,  # معمولاً همان API key است
                'to': phone_number,
                'from': self.sender,
                'text': message,
                'isFlash': False
            }
            
            response = requests.post(url, data=data, timeout=30)
            result = response.json()
            
            if result.get('RetStatus') == 1:
                return {
                    'success': True,
                    'message_id': result.get('StrRetStatus'),
                    'provider_response': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('StrRetStatus', 'Unknown error'),
                    'provider_response': result
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_sms_ir(self, phone_number: str, message: str) -> Dict:
        """ارسال پیامک از طریق SMS.ir"""
        try:
            # دریافت توکن
            auth_url = "https://RestfulSms.com/api/Token"
            auth_data = {
                'UserApiKey': self.api_key,
                'SecretKey': self.api_key  # معمولاً همان API key است
            }
            
            auth_response = requests.post(auth_url, json=auth_data, timeout=30)
            auth_result = auth_response.json()
            
            if auth_result.get('IsSuccessful'):
                token = auth_result.get('TokenKey')
                
                # ارسال پیامک
                send_url = "https://RestfulSms.com/api/MessageSend"
                send_data = {
                    'Messages': [message],
                    'MobileNumbers': [phone_number],
                    'LineNumber': self.sender,
                    'SendDateTime': None,
                    'CanContinueInCaseOfError': False
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'x-sms-ir-secure-token': token
                }
                
                send_response = requests.post(send_url, json=send_data, headers=headers, timeout=30)
                send_result = send_response.json()
                
                if send_result.get('IsSuccessful'):
                    return {
                        'success': True,
                        'message_id': send_result.get('Ids', [None])[0],
                        'provider_response': send_result
                    }
                else:
                    return {
                        'success': False,
                        'error': send_result.get('Message', 'Unknown error'),
                        'provider_response': send_result
                    }
            else:
                return {
                    'success': False,
                    'error': 'Authentication failed',
                    'provider_response': auth_result
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_balance(self) -> Dict:
        """دریافت موجودی"""
        try:
            if self.provider == 'kavenegar':
                return self._get_kavenegar_balance()
            else:
                return {'success': False, 'error': 'Balance check not supported for this provider'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_kavenegar_balance(self) -> Dict:
        """دریافت موجودی کاوه‌نگار"""
        try:
            url = "https://api.kavenegar.com/v1/{}/account/info.json".format(self.api_key)
            response = requests.get(url, timeout=30)
            result = response.json()
            
            if result.get('return', {}).get('status') == 200:
                return {
                    'success': True,
                    'balance': result.get('entries', [{}])[0].get('remaincredit'),
                    'provider_response': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('return', {}).get('message', 'Unknown error')
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

class PasswordManager:
    """مدیریت پسوردها"""
    
    @staticmethod
    def generate_secure_password(length: int = 12, include_special: bool = True) -> str:
        """تولید پسورد امن"""
        import secrets
        import string
        
        if include_special:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        else:
            alphabet = string.ascii_letters + string.digits
        
        # اطمینان از وجود حداقل یک کاراکتر از هر نوع
        password = []
        password.append(secrets.choice(string.ascii_lowercase))
        password.append(secrets.choice(string.ascii_uppercase))
        password.append(secrets.choice(string.digits))
        
        if include_special:
            password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
        
        # پر کردن باقی کاراکترها
        for _ in range(length - len(password)):
            password.append(secrets.choice(alphabet))
        
        # مخلوط کردن
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict:
        """بررسی قدرت پسورد"""
        import re
        
        score = 0
        feedback = []
        
        # طول
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("حداقل 8 کاراکتر")
        
        # حروف کوچک
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("حداقل یک حرف کوچک")
        
        # حروف بزرگ
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("حداقل یک حرف بزرگ")
        
        # اعداد
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("حداقل یک عدد")
        
        # کاراکترهای خاص
        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            score += 1
        else:
            feedback.append("حداقل یک کاراکتر خاص")
        
        # عدم تکرار
        if len(set(password)) >= len(password) * 0.7:
            score += 1
        else:
            feedback.append("کمتر تکرار کاراکتر")
        
        strength = "ضعیف" if score < 3 else "متوسط" if score < 5 else "قوی"
        
        return {
            'score': score,
            'max_score': 6,
            'strength': strength,
            'feedback': feedback,
            'is_strong': score >= 4
        }
