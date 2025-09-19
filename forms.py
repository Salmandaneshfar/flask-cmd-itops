from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SelectField, DateTimeField, FileField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, URL, NumberRange
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('رمز عبور', validators=[DataRequired()])
    remember_me = BooleanField('مرا به خاطر بسپار')

class UserForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تکرار رمز عبور', validators=[DataRequired(), EqualTo('password', message='رمزهای عبور باید یکسان باشند')])
    role = SelectField('نقش', choices=[('user', 'کاربر'), ('editor', 'ویرایشگر'), ('admin', 'مدیر')], default='user')
    is_active = BooleanField('فعال', default=True)
    submit = SubmitField('ذخیره')

class EditUserForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    role = SelectField('نقش', choices=[('user', 'کاربر'), ('editor', 'ویرایشگر'), ('admin', 'مدیر')])
    is_active = BooleanField('فعال')
    new_password = PasswordField('رمز عبور جدید (اختیاری)', validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField('تکرار رمز عبور جدید', validators=[Optional(), EqualTo('new_password', message='رمزهای عبور باید یکسان باشند')])
    submit = SubmitField('ذخیره')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('رمز عبور فعلی', validators=[DataRequired()])
    new_password = PasswordField('رمز عبور جدید', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تکرار رمز عبور جدید', validators=[DataRequired(), EqualTo('new_password', message='رمزهای عبور باید یکسان باشند')])
    submit = SubmitField('تغییر رمز عبور')

class ServerForm(FlaskForm):
    name = StringField('نام سرور', validators=[DataRequired(), Length(min=2, max=100)])
    ip_address = StringField('آدرس IP', validators=[DataRequired()])
    os_type = SelectField('نوع سیستم عامل', choices=[
        ('windows', 'Windows'),
        ('linux', 'Linux'),
        ('macos', 'macOS'),
        ('other', 'سایر')
    ], validators=[DataRequired()])
    status = SelectField('وضعیت', choices=[
        ('active', 'فعال'),
        ('inactive', 'غیرفعال'),
        ('maintenance', 'در حال تعمیر')
    ], validators=[DataRequired()])
    description = TextAreaField('توضیحات', validators=[Optional()])
    submit = SubmitField('ذخیره')

class TaskForm(FlaskForm):
    title = StringField('عنوان تسک', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('توضیحات', validators=[Optional()])
    priority = SelectField('اولویت', choices=[
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'زیاد'),
        ('urgent', 'فوری')
    ], validators=[DataRequired()])
    assigned_to = SelectField('واگذار شده به', coerce=int, validators=[Optional()])
    due_date = DateTimeField('تاریخ سررسید', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField('ذخیره')

class SecurityProjectForm(FlaskForm):
    project_name = StringField('نام پروژه', validators=[DataRequired(), Length(min=3, max=200)])
    contractor = StringField('پیمانکار', validators=[DataRequired(), Length(min=2, max=200)])
    project_type = SelectField('نوع پروژه', choices=[
        ('network', 'شبکه'),
        ('os', 'سیستم عامل'),
        ('application', 'اپلیکیشن'),
        ('database', 'دیتابیس'),
        ('cloud', 'ابر'),
        ('mobile', 'موبایل')
    ], validators=[DataRequired()])
    environment = SelectField('محیط', choices=[
        ('test', 'تست'),
        ('production', 'پروداکشن'),
        ('staging', 'استیجینگ'),
        ('development', 'توسعه')
    ], validators=[DataRequired()])
    security_status = SelectField('وضعیت امنیتی', choices=[
        ('pending', 'در انتظار'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('unknown', 'نامشخص'),
        ('on_hold', 'متوقف شده')
    ], validators=[DataRequired()])
    priority = SelectField('اولویت', choices=[
        ('low', 'پایین'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('critical', 'بحرانی')
    ], validators=[DataRequired()])
    description = TextAreaField('توضیحات پروژه', validators=[Optional()], widget=TextArea())
    security_requirements = TextAreaField('الزامات امنیتی', validators=[Optional()], widget=TextArea())
    vulnerabilities_found = TextAreaField('آسیب‌پذیری‌های یافت شده', validators=[Optional()], widget=TextArea())
    remediation_plan = TextAreaField('برنامه اصلاح', validators=[Optional()], widget=TextArea())
    assigned_to = SelectField('واگذار شده به', coerce=int, validators=[Optional()])
    start_date = DateTimeField('تاریخ شروع', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    estimated_duration = StringField('مدت زمان تخمینی (روز)', validators=[Optional()])
    submit = SubmitField('ذخیره')

class SecurityProjectEditForm(FlaskForm):
    project_name = StringField('نام پروژه', validators=[DataRequired(), Length(min=3, max=200)])
    contractor = StringField('پیمانکار', validators=[DataRequired(), Length(min=2, max=200)])
    project_type = SelectField('نوع پروژه', choices=[
        ('network', 'شبکه'),
        ('os', 'سیستم عامل'),
        ('application', 'اپلیکیشن'),
        ('database', 'دیتابیس'),
        ('cloud', 'ابر'),
        ('mobile', 'موبایل')
    ], validators=[DataRequired()])
    environment = SelectField('محیط', choices=[
        ('test', 'تست'),
        ('production', 'پروداکشن'),
        ('staging', 'استیجینگ'),
        ('development', 'توسعه')
    ], validators=[DataRequired()])
    security_status = SelectField('وضعیت امنیتی', choices=[
        ('pending', 'در انتظار'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('unknown', 'نامشخص'),
        ('on_hold', 'متوقف شده')
    ], validators=[DataRequired()])
    priority = SelectField('اولویت', choices=[
        ('low', 'پایین'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('critical', 'بحرانی')
    ], validators=[DataRequired()])
    description = TextAreaField('توضیحات پروژه', validators=[Optional()], widget=TextArea())
    security_requirements = TextAreaField('الزامات امنیتی', validators=[Optional()], widget=TextArea())
    vulnerabilities_found = TextAreaField('آسیب‌پذیری‌های یافت شده', validators=[Optional()], widget=TextArea())
    remediation_plan = TextAreaField('برنامه اصلاح', validators=[Optional()], widget=TextArea())
    assigned_to = SelectField('واگذار شده به', coerce=int, validators=[Optional()])
    start_date = DateTimeField('تاریخ شروع', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    completion_date = DateTimeField('تاریخ تکمیل', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    estimated_duration = StringField('مدت زمان تخمینی (روز)', validators=[Optional()])
    actual_duration = StringField('مدت زمان واقعی (روز)', validators=[Optional()])
    submit = SubmitField('ذخیره')

class ContentForm(FlaskForm):
    title = StringField('عنوان', validators=[DataRequired(), Length(min=3, max=200)])
    content = TextAreaField('محتوای', validators=[DataRequired()], widget=TextArea())
    slug = StringField('نامک (Slug)', validators=[DataRequired(), Length(min=3, max=200)])
    content_type = SelectField('نوع محتوا', choices=[
        ('page', 'صفحه'),
        ('post', 'مطلب'),
        ('article', 'مقاله')
    ], validators=[DataRequired()])
    status = SelectField('وضعیت', choices=[
        ('draft', 'پیش‌نویس'),
        ('published', 'منتشر شده'),
        ('archived', 'آرشیو شده')
    ], validators=[DataRequired()])
    submit = SubmitField('ذخیره')

class BackupForm(FlaskForm):
    name = StringField('نام بکاپ', validators=[DataRequired(), Length(min=3, max=200)])
    file_path = StringField('مسیر فایل', validators=[DataRequired(), Length(min=3, max=500)])
    file_size = StringField('حجم فایل (بایت)', validators=[Optional()])
    backup_type = SelectField('نوع بکاپ', choices=[
        ('database', 'دیتابیس'),
        ('files', 'فایل‌ها'),
        ('full', 'کامل')
    ], validators=[DataRequired()])
    status = SelectField('وضعیت', choices=[
        ('pending', 'در انتظار'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق')
    ], validators=[DataRequired()])
    submit = SubmitField('ذخیره')

## SearchForm removed per product decision

class CustomFieldForm(FlaskForm):
    name = StringField('نام فیلد (انگلیسی)', validators=[DataRequired(), Length(min=2, max=100)])
    label = StringField('برچسب فیلد (فارسی)', validators=[DataRequired(), Length(min=2, max=200)])
    field_type = SelectField('نوع فیلد', choices=[
        ('text', 'متن'),
        ('number', 'عدد'),
        ('email', 'ایمیل'),
        ('date', 'تاریخ'),
        ('select', 'انتخاب از لیست'),
        ('textarea', 'متن طولانی'),
        ('checkbox', 'چک باکس'),
        ('url', 'لینک'),
        ('phone', 'شماره تلفن')
    ], validators=[DataRequired()])
    model_name = SelectField('مدل مربوطه', choices=[
        ('User', 'کاربران'),
        ('Server', 'سرورها'),
        ('Task', 'تسک‌ها'),
        ('Content', 'محتوا'),
        ('Backup', 'بکاپ‌ها'),
        ('SecurityProject', 'پروژه‌های امنیتی'),
        ('Credential', 'اعتبارنامه‌ها'),
        ('Bookmark', 'نشانک‌ها'),
        ('Person', 'اشخاص'),
        ('Attachment', 'پیوست‌ها'),
        ('LookupItem', 'آیتم‌های مرجع')
    ], validators=[DataRequired()])
    is_required = BooleanField('اجباری')
    is_active = BooleanField('فعال', default=True)
    placeholder = StringField('متن راهنما', validators=[Optional(), Length(max=200)])
    help_text = TextAreaField('راهنمای اضافی', validators=[Optional()])
    order = StringField('ترتیب نمایش', validators=[Optional()], default='0')
    options = TextAreaField('گزینه‌های انتخابی (هر خط یک گزینه)', validators=[Optional()])
    submit = SubmitField('ذخیره')

class CustomFieldEditForm(FlaskForm):
    label = StringField('برچسب فیلد (فارسی)', validators=[DataRequired(), Length(min=2, max=200)])
    field_type = SelectField('نوع فیلد', choices=[
        ('text', 'متن'),
        ('number', 'عدد'),
        ('email', 'ایمیل'),
        ('date', 'تاریخ'),
        ('select', 'انتخاب از لیست'),
        ('textarea', 'متن طولانی'),
        ('checkbox', 'چک باکس'),
        ('url', 'لینک'),
        ('phone', 'شماره تلفن')
    ], validators=[DataRequired()])
    is_required = BooleanField('اجباری')
    is_active = BooleanField('فعال')
    placeholder = StringField('متن راهنما', validators=[Optional(), Length(max=200)])
    help_text = TextAreaField('راهنمای اضافی', validators=[Optional()])
    order = StringField('ترتیب نمایش', validators=[Optional()])
    options = TextAreaField('گزینه‌های انتخابی (هر خط یک گزینه)', validators=[Optional()], render_kw={'rows': 4, 'placeholder': 'هر خط یک گزینه\nمثال:\nگزینه 1\nگزینه 2\nگزینه 3'})
    submit = SubmitField('ذخیره')

# فرم‌های مدیریت رمزها
class CredentialForm(FlaskForm):
    name = StringField('نام سرویس/اپلیکیشن', validators=[DataRequired(), Length(min=2, max=200)])
    service_type = SelectField('نوع سرویس', choices=[
        ('server', 'سرور'),
        ('database', 'دیتابیس'),
        ('application', 'اپلیکیشن'),
        ('email', 'ایمیل'),
        ('cloud', 'کلود'),
        ('social', 'شبکه اجتماعی'),
        ('payment', 'درگاه پرداخت'),
        ('other', 'سایر')
    ], validators=[DataRequired()])
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=1, max=200)])
    password = PasswordField('رمز عبور', validators=[DataRequired(), Length(min=6)])
    url = StringField('آدرس سرویس', validators=[Optional()])
    description = TextAreaField('توضیحات', validators=[Optional()])
    tags = StringField('برچسب‌ها (با کاما جدا کنید)', validators=[Optional()])
    is_active = BooleanField('فعال', default=True)
    submit = SubmitField('ذخیره')

class CredentialEditForm(FlaskForm):
    name = StringField('نام سرویس/اپلیکیشن', validators=[DataRequired(), Length(min=2, max=200)])
    service_type = SelectField('نوع سرویس', choices=[
        ('server', 'سرور'),
        ('database', 'دیتابیس'),
        ('application', 'اپلیکیشن'),
        ('email', 'ایمیل'),
        ('cloud', 'کلود'),
        ('social', 'شبکه اجتماعی'),
        ('payment', 'درگاه پرداخت'),
        ('other', 'سایر')
    ], validators=[DataRequired()])
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=1, max=200)])
    password = PasswordField('رمز عبور جدید (خالی بگذارید اگر تغییر نمی‌دهید)', validators=[Optional(), Length(min=6)])
    url = StringField('آدرس سرویس', validators=[Optional()])
    description = TextAreaField('توضیحات', validators=[Optional()])
    tags = StringField('برچسب‌ها (با کاما جدا کنید)', validators=[Optional()])
    is_active = BooleanField('فعال', default=True)
    submit = SubmitField('ذخیره')

class CredentialSearchForm(FlaskForm):
    query = StringField('جستجو', validators=[Optional()])
    service_type = SelectField('نوع سرویس', choices=[
        ('', 'همه'),
        ('server', 'سرور'),
        ('database', 'دیتابیس'),
        ('application', 'اپلیکیشن'),
        ('email', 'ایمیل'),
        ('cloud', 'کلود'),
        ('social', 'شبکه اجتماعی'),
        ('payment', 'درگاه پرداخت'),
        ('other', 'سایر')
    ], validators=[Optional()])
    tags = StringField('برچسب', validators=[Optional()])
    submit = SubmitField('جستجو')


class BookmarkForm(FlaskForm):
    name = StringField('نام سرویس/نشانه', validators=[DataRequired(), Length(min=2, max=200)])
    address = StringField('آدرس یا دامنه/IP', validators=[Optional(), Length(max=500)])
    port = IntegerField('پورت', validators=[Optional(), NumberRange(min=1, max=65535)])
    url = StringField('لینک کامل (اختیاری)', validators=[Optional(), URL()])
    description = TextAreaField('توضیحات', validators=[Optional()])
    is_favorite = BooleanField('علاقه‌مندی')
    submit = SubmitField('ذخیره')


class BookmarkEditForm(FlaskForm):
    name = StringField('نام سرویس/نشانه', validators=[DataRequired(), Length(min=2, max=200)])
    address = StringField('آدرس یا دامنه/IP', validators=[Optional(), Length(max=500)])
    port = IntegerField('پورت', validators=[Optional(), NumberRange(min=1, max=65535)])
    url = StringField('لینک کامل (اختیاری)', validators=[Optional(), URL()])
    description = TextAreaField('توضیحات', validators=[Optional()])
    is_favorite = BooleanField('علاقه‌مندی')
    submit = SubmitField('ذخیره')


class PersonForm(FlaskForm):
    category = SelectField('دسته‌بندی', choices=[('internal', 'داخلی'), ('external', 'سایر ادارات')], validators=[DataRequired()])
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=1, max=120)])
    dongle_name = StringField('نام دانگل', validators=[Optional(), Length(max=120)])
    phone = StringField('شماره تماس', validators=[Optional(), Length(max=50)])
    department = SelectField('واحد/اداره', choices=[], validators=[Optional()])
    description = TextAreaField('توضیحات', validators=[Optional()])
    submit = SubmitField('ذخیره')

class PersonEditForm(FlaskForm):
    category = SelectField('دسته‌بندی', choices=[('internal', 'داخلی'), ('external', 'سایر ادارات')], validators=[DataRequired()])
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=1, max=120)])
    dongle_name = StringField('نام دانگل', validators=[Optional(), Length(max=120)])
    phone = StringField('شماره تماس', validators=[Optional(), Length(max=50)])
    department = SelectField('واحد/اداره', choices=[], validators=[Optional()])
    description = TextAreaField('توضیحات', validators=[Optional()])
    submit = SubmitField('ذخیره')
