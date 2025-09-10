from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    accounts = db.relationship('InstagramAccount', backref='owner', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class InstagramAccount(db.Model):
    __tablename__ = 'instagram_accounts'
    id = db.Column(db.Integer, primary_key=True)
    # For simplicity, we are not encrypting the cookie. 
    # WARNING: For a real-world application, you MUST encrypt this data.
    cookie_string = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # A helper property to get the username from the cookie if possible
    @property
    def username(self):
        for part in self.cookie_string.split(';'):
            if 'ds_user=' in part:
                return part.strip().split('=')[1]
        return "Unknown"
