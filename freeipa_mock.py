"""
FreeIPA Mock Service برای تست
"""

class FreeIPAMockService:
    """سرویس Mock FreeIPA برای تست"""
    
    def __init__(self):
        self.mock_users = [
            {
                'username': 'admin',
                'full_name': 'Administrator',
                'email': 'admin@mci.local',
                'first_name': 'Admin',
                'last_name': 'User',
                'groups': ['admins', 'users']
            },
            {
                'username': 'mci',
                'full_name': 'MCI User',
                'email': 'mci@mci.local',
                'first_name': 'MCI',
                'last_name': 'User',
                'groups': ['admins', 'users']
            },
            {
                'username': 'john.doe',
                'full_name': 'John Doe',
                'email': 'john.doe@mci.local',
                'first_name': 'John',
                'last_name': 'Doe',
                'groups': ['developers', 'users']
            }
        ]
    
    def authenticate_user(self, username, password):
        """احراز هویت کاربر (Mock)"""
        # برای تست، هر کاربری با هر رمزی وارد می‌شود
        for user in self.mock_users:
            if user['username'] == username:
                return True, user
        return False, None
    
    def get_user_info(self, username):
        """دریافت اطلاعات کاربر (Mock)"""
        for user in self.mock_users:
            if user['username'] == username:
                return user
        return None
    
    def get_all_users(self):
        """دریافت لیست تمام کاربران (Mock)"""
        return self.mock_users
    
    def get_user_groups(self, username):
        """دریافت گروه‌های کاربر (Mock)"""
        user = self.get_user_info(username)
        if user:
            return user.get('groups', [])
        return []
    
    def is_user_in_group(self, username, group_name):
        """بررسی عضویت کاربر در گروه (Mock)"""
        groups = self.get_user_groups(username)
        return group_name in groups
    
    def test_connection(self):
        """تست اتصال (Mock)"""
        return True, "اتصال Mock موفق - FreeIPA در حالت تست"

# ایجاد instance سراسری
freeipa_mock_service = FreeIPAMockService()
