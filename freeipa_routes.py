"""
Route های FreeIPA برای Flask CMS
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from freeipa_service import freeipa_service
import logging

logger = logging.getLogger(__name__)

# ایجاد Blueprint
freeipa_bp = Blueprint('freeipa', __name__, url_prefix='/freeipa')

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
    
    return redirect(url_for('admin.index'))

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
