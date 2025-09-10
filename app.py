import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, bcrypt, User, InstagramAccount
import instagram_logic

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_development')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Username or email already exists.', 'warning')
            return redirect(url_for('register'))
            
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    accounts = InstagramAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', accounts=accounts)

@app.route('/add_account', methods=['POST'])
@login_required
def add_account():
    cookie_string = request.form.get('cookie_string')
    if cookie_string:
        new_account = InstagramAccount(cookie_string=cookie_string, owner=current_user)
        db.session.add(new_account)
        db.session.commit()
        flash('Instagram account added successfully!', 'success')
    else:
        flash('Cookie string cannot be empty.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/delete_account/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id):
    account = InstagramAccount.query.get_or_404(account_id)
    if account.user_id != current_user.id:
        flash('You do not have permission to delete this account.', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(account)
    db.session.commit()
    flash('Account deleted successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/perform_action', methods=['POST'])
@login_required
def perform_action():
    action = request.form.get('action')
    target = request.form.get('target')
    comment = request.form.get('comment_text', '')
    account_id = request.form.get('account_id')

    account = InstagramAccount.query.get(account_id)
    if not account or account.user_id != current_user.id:
        flash('Invalid account selected.', 'danger')
        return redirect(url_for('dashboard'))

    cookie = account.cookie_string
    success = False
    
    # WARNING: These actions run directly and will block the server.
    # For a real app, use a background task queue like Celery.
    if action == 'follow':
        success = instagram_logic.follow_user(target, cookie)
    elif action == 'like':
        success = instagram_logic.like_post(target, cookie)
    elif action == 'comment':
        success = instagram_logic.comment_post(target, comment, cookie)
    elif action == 'scrape':
        profile_data = instagram_logic.get_instagram_profile_info(target, cookie)
        if profile_data:
            flash(f"Scrape Success! User: {profile_data.get('full_name')}, Followers: {profile_data.get('edge_followed_by', {}).get('count')}", 'info')
            return redirect(url_for('dashboard'))
        else:
            success = False

    if success:
        flash(f'Action "{action}" on "{target}" completed successfully!', 'success')
    else:
        flash(f'Action "{action}" on "{target}" failed. The account may be rate-limited or the cookie invalid.', 'danger')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
  
