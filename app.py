from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cms.db'
db = SQLAlchemy(app)

# رمزنگاری
key = Fernet.generate_key()
cipher = Fernet(key)

# مدل رمزها
class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(100))
    username = db.Column(db.String(100))
    password_encrypted = db.Column(db.String(200))

    def set_password(self, raw_password):
        self.password_encrypted = cipher.encrypt(raw_password.encode()).decode()

    def get_password(self):
        return cipher.decrypt(self.password_encrypted.encode()).decode()

# مدل سرورها
class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    os_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/credentials', methods=['GET', 'POST'])
def credentials():
    if request.method == 'POST':
        app_name = request.form['app_name']
        username = request.form['username']
        password = request.form['password']
        cred = Credential(app_name=app_name, username=username)
        cred.set_password(password)
        db.session.add(cred)
        db.session.commit()
        return redirect(url_for('credentials'))
    
    creds = Credential.query.all()
    return render_template('credentials.html', credentials=creds)

@app.route('/servers', methods=['GET', 'POST'])
def servers():
    if request.method == 'POST':
        name = request.form['name']
        ip = request.form['ip_address']
        os_type = request.form['os_type']
        status = request.form['status']
        server = Server(name=name, ip_address=ip, os_type=os_type, status=status)
        db.session.add(server)
        db.session.commit()
        return redirect(url_for('servers'))

    server_list = Server.query.all()
    return render_template('servers.html', servers=server_list)

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    # فعلاً بدون دیتابیس، فقط نمایش قالب
    return render_template('tasks.html', tasks=[])

@app.route('/backups', methods=['GET', 'POST'])
def backups():
    # فعلاً بدون دیتابیس، فقط نمایش قالب
    return render_template('backups.html', backups=[])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
