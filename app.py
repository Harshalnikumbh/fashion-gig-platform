# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from database import db, User
from dashboard_routes import dashboard_bp
from flask_bcrypt import Bcrypt
import os

load_dotenv()

app = Flask(__name__, template_folder='templates')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-secret')

db.init_app(app)
bcrypt = Bcrypt(app)

app.register_blueprint(dashboard_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

#  SIGNIN — GET shows page, POST handles login 
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('signin.html')

    # POST — handle login
    data     = request.get_json(silent=True) or request.form
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    # Store user in session
    session['user'] = {
        "user_id":    user.user_id,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "email":      user.email,
        "role":       user.role,
    }

    return jsonify({"success": True, "redirect": "/dashboard"})

#  LOGOUT 
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('signin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True')