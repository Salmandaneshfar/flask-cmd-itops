"""
Route های FreeIPA برای Flask CMS
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
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

@freeipa_bp.route('/user/<username>/group/add', methods=['POST'])
def add_user_to_group_action(username):
    try:
        group_cn = request.form.get('group_cn')
        if not group_cn:
            flash('نام گروه وارد نشده است', 'error')
            return redirect(url_for('freeipa.user_info', username=username))
        ok = freeipa_service.add_user_to_group(username, group_cn)
        flash('کاربر به گروه افزوده شد' if ok else 'خطا در افزودن به گروه', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

@freeipa_bp.route('/user/<username>/group/remove', methods=['POST'])
def remove_user_from_group_action(username):
    try:
        group_cn = request.form.get('group_cn')
        if not group_cn:
            flash('نام گروه وارد نشده است', 'error')
            return redirect(url_for('freeipa.user_info', username=username))
        ok = freeipa_service.remove_user_from_group(username, group_cn)
        flash('کاربر از گروه حذف شد' if ok else 'خطا در حذف از گروه', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

@freeipa_bp.route('/user/<username>/password/reset', methods=['POST'])
def reset_user_password_action(username):
    try:
        import secrets, string
        new_password = request.form.get('new_password', '').strip()
        if not new_password:
            alphabet = string.ascii_letters + string.digits + '!@#$%^&*()'
            new_password = ''.join(secrets.choice(alphabet) for _ in range(12))
        ok, msg = freeipa_service.set_user_password(username, new_password)
        if ok:
            from models import db, FreeIPAUser, UserPassword
            freeipa_user = FreeIPAUser.query.filter_by(uid=username).first()
            if not freeipa_user:
                freeipa_user = FreeIPAUser(uid=username, cn=username, sn=username, givenname=username, mail='')
                db.session.add(freeipa_user)
                db.session.flush()
            up = UserPassword(user_id=freeipa_user.id, password_type='reset', created_by=1)
            up.set_password(new_password)
            db.session.add(up)
            db.session.commit()
            flash('پسورد ریست شد و برای ارسال/مرجع ذخیره شد', 'success')
        else:
            flash(f'خطا در ریست پسورد: {msg}', 'error')
    except Exception as e:
        from models import db
        db.session.rollback()
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

@freeipa_bp.route('/user/<username>/password/relax', methods=['POST'])
def relax_user_password_policy_action(username):
    try:
        ok = freeipa_service.relax_password_policy(username)
        flash('سیاست رمز برای کاربر به‌روزرسانی شد' if ok else 'خطا در به‌روزرسانی سیاست رمز', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

@freeipa_bp.route('/user/<username>/principal-exp', methods=['POST'])
def set_principal_expiration_action(username):
    try:
        zulu = request.form.get('krb_principal_exp')
        clear = request.form.get('clear_exp')
        rel_days = request.form.get('relative_days')
        rel_hours = request.form.get('relative_hours')
        if clear == '1' or (zulu and zulu.strip() == ''):
            ok = freeipa_service.unset_principal_expiration(username)
        elif rel_days or rel_hours:
            now = datetime.utcnow()
            delta = timedelta(days=int(rel_days or 0), hours=int(rel_hours or 0))
            target = now + delta
            zulu_calc = target.strftime('%Y%m%d%H%M%SZ')
            ok = freeipa_service.set_principal_expiration(username, zulu_calc)
        else:
            ok = freeipa_service.set_principal_expiration(username, zulu.strip())
        flash('Kerberos principal expiration به‌روزرسانی شد' if ok else 'خطا در به‌روزرسانی expiration', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

@freeipa_bp.route('/user/<username>/delete', methods=['POST'])
def delete_user_action(username):
    """حذف کاربر از FreeIPA"""
    try:
        # حذف از LDAP
        cfg = freeipa_service._get_config()
        from ldap3 import SUBTREE
        conn = freeipa_service._get_connection()
        if not conn or not conn.bind():
            flash('اتصال به FreeIPA برقرار نشد', 'error')
            return redirect(url_for('freeipa.list_users'))
        user_dn = f"uid={username},cn=users,cn=accounts,{cfg['base_dn']}"
        ok = conn.delete(user_dn)
        conn.unbind()
        flash('کاربر حذف شد' if ok else 'حذف کاربر ناموفق بود', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.list_users'))

@freeipa_bp.route('/user/<username>/enable', methods=['POST'])
def enable_user_action(username):
    try:
        ok = freeipa_service.enable_user(username)
        flash('کاربر فعال شد' if ok else 'خطا در فعال‌سازی کاربر', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

@freeipa_bp.route('/user/<username>/disable', methods=['POST'])
def disable_user_action(username):
    try:
        ok = freeipa_service.disable_user(username)
        flash('کاربر غیرفعال شد' if ok else 'خطا در غیرفعال‌سازی کاربر', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

@freeipa_bp.route('/user/<username>/unlock', methods=['POST'])
def unlock_user_action(username):
    try:
        ok = freeipa_service.unlock_user(username)
        flash('قفل کاربر باز شد' if ok else 'خطا در Unlock کاربر', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

@freeipa_bp.route('/user/<username>/lock', methods=['POST'])
def lock_user_action(username):
    try:
        ok = freeipa_service.lock_user(username)
        flash('کاربر قفل شد' if ok else 'خطا در Lock کاربر', 'success' if ok else 'error')
    except Exception as e:
        flash(f'خطا: {e}', 'error')
    return redirect(url_for('freeipa.user_info', username=username))

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
        up.set_password(password)
        db.session.add(up)
        db.session.commit()

        flash('کاربر با موفقیت ایجاد شد و پسورد برای ارسال SMS ذخیره شد', 'success')
        return redirect(url_for('freeipa.list_users'))

    except Exception as e:
        from models import db
        db.session.rollback()
        flash(f'خطا: {e}', 'error')
        return redirect(url_for('freeipa.add_user'))

@freeipa_bp.route('/servers', methods=['GET', 'POST'])
def servers():
    """تنظیمات سرور FreeIPA: مشاهده/ذخیره و تست اتصال"""
    try:
        from flask import current_app
        import os
        cfg = {
            'host': current_app.config.get('FREEIPA_HOST', ''),
            'port': current_app.config.get('FREEIPA_PORT', 389),
            'use_ssl': current_app.config.get('FREEIPA_USE_SSL', False),
            'base_dn': current_app.config.get('FREEIPA_BASE_DN', ''),
            'bind_dn': current_app.config.get('FREEIPA_BIND_DN', ''),
            'bind_password': current_app.config.get('FREEIPA_BIND_PASSWORD', ''),
        }
        if request.method == 'POST':
            action = request.form.get('action', 'save')
            new_cfg = {
                'FREEIPA_HOST': request.form.get('host', cfg['host']).strip(),
                'FREEIPA_PORT': int(request.form.get('port', cfg['port'])),
                'FREEIPA_USE_SSL': 'true' if request.form.get('use_ssl') in ['1', 'true', 'on'] else 'false',
                'FREEIPA_BASE_DN': request.form.get('base_dn', cfg['base_dn']).strip(),
                'FREEIPA_BIND_DN': request.form.get('bind_dn', cfg['bind_dn']).strip(),
                'FREEIPA_BIND_PASSWORD': request.form.get('bind_password', cfg['bind_password']),
            }
            # به‌روزرسانی config در حال اجرا
            for k, v in new_cfg.items():
                if k == 'FREEIPA_PORT':
                    current_app.config[k] = int(v)
                elif k == 'FREEIPA_USE_SSL':
                    current_app.config[k] = (str(v).lower() in ['true', '1', 'on'])
                else:
                    current_app.config[k] = v
            # ذخیره در فایل env محلی (اختیاری / در .gitignore)
            try:
                env_path = os.path.join(current_app.root_path, 'freeipa_config.env')
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join([
                        f"FREEIPA_HOST={new_cfg['FREEIPA_HOST']}",
                        f"FREEIPA_PORT={new_cfg['FREEIPA_PORT']}",
                        f"FREEIPA_USE_SSL={new_cfg['FREEIPA_USE_SSL']}",
                        f"FREEIPA_BASE_DN={new_cfg['FREEIPA_BASE_DN']}",
                        f"FREEIPA_BIND_DN={new_cfg['FREEIPA_BIND_DN']}",
                        f"FREEIPA_BIND_PASSWORD={new_cfg['FREEIPA_BIND_PASSWORD']}"
                    ]))
                flash('تنظیمات ذخیره شد', 'success')
            except Exception as e:
                flash(f'ذخیره فایل تنظیمات ناموفق بود: {e}', 'error')
            if action == 'test':
                ok, msg = freeipa_service.test_connection()
                flash(msg, 'success' if ok else 'error')
        # بازخوانی برای نمایش
        cfg = {
            'host': current_app.config.get('FREEIPA_HOST', ''),
            'port': current_app.config.get('FREEIPA_PORT', 389),
            'use_ssl': current_app.config.get('FREEIPA_USE_SSL', False),
            'base_dn': current_app.config.get('FREEIPA_BASE_DN', ''),
            'bind_dn': current_app.config.get('FREEIPA_BIND_DN', ''),
            'bind_password': current_app.config.get('FREEIPA_BIND_PASSWORD', ''),
        }
        return render_template('freeipa/servers.html', cfg=cfg)
    except Exception as e:
        flash(f'خطا در نمایش/ذخیره تنظیمات سرور: {e}', 'error')
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
