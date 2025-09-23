"""
Route های FreeIPA برای Flask CMS
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from freeipa_service import freeipa_service
import logging

logger = logging.getLogger(__name__)

# ایجاد Blueprint
freeipa_bp = Blueprint('freeipa', __name__, url_prefix='/freeipa')

@freeipa_bp.route('/')
def dashboard():
    """صفحه اصلی FreeIPA با منوی تب‌های سمت چپ"""
    return render_template('freeipa/portal.html')

@freeipa_bp.route('/test')
def test_connection():
    """تست اتصال به FreeIPA"""
    try:
        success, message = freeipa_service.test_connection()
        if success:
            flash('اتصال به FreeIPA موفق بود!', 'success')
        else:
            flash(f'خطا در اتصال به FreeIPA: {message}', 'error')
    except Exception as e:
        flash(f'خطا در تست اتصال: {e}', 'error')
    
    return redirect(url_for('freeipa.dashboard'))

@freeipa_bp.route('/users')
def list_users():
    """لیست کاربران FreeIPA"""
    try:
        users = freeipa_service.get_all_users()
        return render_template('freeipa/users.html', users=users)
    except Exception as e:
        flash(f'خطا در دریافت لیست کاربران: {e}', 'error')
        return redirect(url_for('index'))

@freeipa_bp.route('/user/<username>')
def user_info(username):
    """اطلاعات کاربر FreeIPA"""
    try:
        user_info = freeipa_service.get_user_info(username)
        if user_info:
            return render_template('freeipa/user_info.html', user=user_info)
        else:
            flash(f'کاربر {username} یافت نشد', 'error')
            return redirect(url_for('freeipa.list_users'))
    except Exception as e:
        flash(f'خطا در دریافت اطلاعات کاربر: {e}', 'error')
        return redirect(url_for('freeipa.list_users'))

@freeipa_bp.route('/groups')
def groups():
    """نمایش گروه‌ها (الگو موجود)"""
    try:
        groups = freeipa_service.get_all_groups()
        return render_template('freeipa/groups.html', groups=groups)
    except Exception as e:
        flash(f'خطا در نمایش گروه‌ها: {e}', 'error')
        return redirect(url_for('freeipa.dashboard'))

@freeipa_bp.route('/groups/add', methods=['GET'])
def add_group():
    """افزودن گروه (فرم نمایشی)"""
    try:
        return render_template('freeipa/add_group.html')
    except Exception as e:
        flash(f'خطا در نمایش فرم گروه: {e}', 'error')
        return redirect(url_for('freeipa.dashboard'))

@freeipa_bp.route('/users/add', methods=['GET', 'POST'])
def add_user():
    """افزودن کاربر (فرم + ایجاد در FreeIPA و ذخیره پسورد برای SMS)"""
    try:
        if request.method == 'GET':
            groups = freeipa_service.get_all_groups()
            return render_template('freeipa/add_user.html', groups=groups)

        # POST
        uid = request.form.get('uid', '').strip()
        mail = request.form.get('mail', '').strip()
        givenname = request.form.get('givenname', '').strip()
        sn = request.form.get('sn', '').strip()
        cn = request.form.get('cn', '').strip()
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '').strip()
        selected_groups = request.form.getlist('groups')

        if not uid or not mail or not givenname or not sn or not cn:
            flash('فیلدهای ضروری را تکمیل کنید', 'error')
            return redirect(url_for('freeipa.add_user'))

        if not password:
            import secrets, string
            alphabet = string.ascii_letters + string.digits + '!@#$%^&*()'
            password = ''.join(secrets.choice(alphabet) for _ in range(12))

        # ایجاد کاربر در FreeIPA با ldap3
        from ldap3 import MODIFY_ADD
        cfg = freeipa_service._get_config()
        server = freeipa_service._get_connection().server
        conn = freeipa_service._get_connection()
        if not conn or not conn.bind():
            flash('اتصال به FreeIPA برقرار نشد', 'error')
            return redirect(url_for('freeipa.add_user'))

        user_dn = f"uid={uid},cn=users,cn=accounts,{cfg['base_dn']}"
        attrs = {
            'objectClass': ['inetOrgPerson', 'posixAccount', 'top', 'person', 'organizationalPerson', 'krbPrincipalAux', 'inetUser'],
            'uid': uid,
            'cn': cn,
            'sn': sn,
            'givenName': givenname,
            'mail': mail,
            'loginShell': '/bin/bash',
            'homeDirectory': f"/home/{uid}",
            'uidNumber': '10000',
            'gidNumber': '10000',
            'userPassword': password,
            'krbPrincipalName': f"{uid}@{cfg['base_dn'].replace('dc=','').replace(',', '.').upper()}"
        }
        if mobile:
            attrs['mobile'] = mobile

        ok = conn.add(user_dn, attributes=attrs)
        if not ok:
            err = conn.result or {}
            conn.unbind()
            flash(f"خطا در ایجاد کاربر: {err}", 'error')
            return redirect(url_for('freeipa.add_user'))

        # افزودن به گروه‌ها
        for cn_group in selected_groups:
            group_dn = f"cn={cn_group},cn=groups,cn=accounts,{cfg['base_dn']}"
            conn.modify(group_dn, {'member': [(MODIFY_ADD, [user_dn])]})

        # تنظیم پسورد Kerberos (اختیاری)
        # در صورت نیاز: conn.extend.novell.set_password(user_dn, password)

        conn.unbind()

        # ذخیره پسورد برای SMS در DB (متن‌واضح برای ارسال بعدی)
        from models import db, FreeIPAUser, UserPassword
        freeipa_user = FreeIPAUser(uid=uid, cn=cn, sn=sn, givenname=givenname, mail=mail, mobile=mobile)
        db.session.add(freeipa_user)
        db.session.flush()
        up = UserPassword(user_id=freeipa_user.id, password_type='initial', created_by=1)  # TODO: current_user.id
        up.set_password_raw(password)
        db.session.add(up)
        db.session.commit()

        flash('کاربر با موفقیت ایجاد شد و پسورد برای ارسال SMS ذخیره شد', 'success')
        return redirect(url_for('freeipa.list_users'))

    except Exception as e:
        from models import db
        db.session.rollback()
        flash(f'خطا: {e}', 'error')
        return redirect(url_for('freeipa.add_user'))

@freeipa_bp.route('/servers')
def servers():
    """تنظیمات سرور (الگو موجود)"""
    try:
        return render_template('freeipa/servers.html')
    except Exception as e:
        flash(f'خطا در نمایش تنظیمات سرور: {e}', 'error')
        return redirect(url_for('freeipa.dashboard'))

@freeipa_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ورود با FreeIPA"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            try:
                success, user_info = freeipa_service.authenticate_user(username, password)
                if success:
                    flash(f'ورود موفق! خوش آمدید {user_info["full_name"]}', 'success')
                    # اینجا می‌توانید session را تنظیم کنید
                    return redirect(url_for('index'))
                else:
                    flash('نام کاربری یا رمز عبور اشتباه است', 'error')
            except Exception as e:
                flash(f'خطا در ورود: {e}', 'error')
        else:
            flash('لطفاً نام کاربری و رمز عبور را وارد کنید', 'error')
    
    return render_template('freeipa/login.html')

@freeipa_bp.route('/api/test')
def api_test_connection():
    """API تست اتصال"""
    try:
        success, message = freeipa_service.test_connection()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@freeipa_bp.route('/api/users')
def api_list_users():
    """API لیست کاربران"""
    try:
        users = freeipa_service.get_all_users()
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@freeipa_bp.route('/api/user/<username>')
def api_user_info(username):
    """API اطلاعات کاربر"""
    try:
        user_info = freeipa_service.get_user_info(username)
        if user_info:
            return jsonify({
                'success': True,
                'user': user_info
            })
        else:
            return jsonify({
                'success': False,
                'message': 'کاربر یافت نشد'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
