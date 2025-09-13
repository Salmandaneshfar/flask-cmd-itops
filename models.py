from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    os_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # فعال، غیرفعال، در حال بررسی
