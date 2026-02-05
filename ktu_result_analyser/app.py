import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils.pdf_processor import process_pdf, generate_stats
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import pandas as pd
import shutil
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_change_me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = None

# Mail Configuration (Example - Update with real SMTP)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

HISTORY_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'history.json')

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# History Management Helpers
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r') as f:
            all_history = json.load(f)
            # Filter history by current user if logged in
            if current_user.is_authenticated:
                return [h for h in all_history if h.get('user_id') == current_user.id]
            return []
    except:
        return []

def save_history(history):
    all_history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                all_history = json.load(f)
        except:
            pass
    
    user_id = current_user.id if current_user.is_authenticated else None
    rest_history = [h for h in all_history if h.get('user_id') != user_id]
    
    for h in history:
        h['user_id'] = user_id
        
    all_history = history + rest_history
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(all_history, f, indent=4)

def add_to_history(filename, excel_filename):
    history = load_history()
    entry = {
        'id': str(uuid.uuid4()),
        'user_id': current_user.id,
        'filename': filename,
        'excel_filename': excel_filename,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    history.insert(0, entry)
    save_history(history)
    return entry

def delete_from_history(entry_id):
    all_history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                all_history = json.load(f)
        except:
            pass
            
    entry = next((item for item in all_history if item['id'] == entry_id and item.get('user_id') == current_user.id), None)
    
    if entry:
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], entry['excel_filename'])
        if os.path.exists(excel_path):
            os.remove(excel_path)
            
        all_history = [item for item in all_history if item['id'] != entry_id]
        with open(HISTORY_FILE, 'w') as f:
            json.dump(all_history, f, indent=4)

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.password and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered')
            return redirect(url_for('signup'))
            
        new_user = User(email=email, name=name, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    history = load_history()
    return render_template('index.html', history=history, user=current_user)

@app.route('/calculator')
@login_required
def calculator():
    return render_template('calculator.html', user=current_user)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{current_user.id}_{file.filename}")
        file.save(filepath)
        
        df, stats = process_pdf(filepath)
        
        if df is None:
            return "Error processing PDF or no data found. Please check format.", 400
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"user_{current_user.id}_analysis_{timestamp}.xlsx"
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All Results', index=False)
            
            if 'Dept' in df.columns and 'Year' in df.columns:
                # 1. Generate Summary Analytics Sheet
                summary_data = []
                for dept in stats['departments']:
                    for year, subjects in stats['dept_sub_stats'][dept].items():
                        for sub_code, sub_data in subjects.items():
                            pass_p = (sub_data['pass'] / sub_data['total'] * 100) if sub_data['total'] > 0 else 0
                            summary_data.append({
                                'Department': dept,
                                'Admission Year': year,
                                'Subject Code': sub_code,
                                'Passed': sub_data['pass'],
                                'Failed/Abs': sub_data['fail'],
                                'Total': sub_data['total'],
                                'Pass %': round(pass_p, 2)
                            })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary Analytics', index=False)

                # 2. Generate Individual Dept_Year Sheets
                groups = df[['Dept', 'Year']].drop_duplicates()
                groups = groups.sort_values(by=['Dept', 'Year'])
                for _, row in groups.iterrows():
                    dept = row['Dept']
                    year = row['Year']
                    group_df = df[(df['Dept'] == dept) & (df['Year'] == year)]
                    if not group_df.empty:
                        pivot_df = group_df.pivot_table(index='Register No', columns='Subject', values='Grade', aggfunc='first')
                        pivot_df = pivot_df.fillna('-')
                        sheet_name = f"{dept}_{year}"[:31]
                        pivot_df.to_excel(writer, sheet_name=sheet_name)
        
        add_to_history(file.filename, excel_filename)
        
        # Latest copy for results page
        latest_path = os.path.join(app.config['UPLOAD_FOLDER'], f'latest_{current_user.id}.xlsx')
        shutil.copy2(excel_path, latest_path)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return render_template('results.html', stats=stats, df=df, user=current_user, filename=file.filename)
    
    return "Invalid file format. Please upload a PDF.", 400

@app.route('/view/<entry_id>')
@login_required
def view_analysis(entry_id):
    history = load_history()
    entry = next((item for item in history if str(item['id']) == entry_id), None)
    
    if not entry:
        return "Analysis not found", 404
        
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], entry['excel_filename'])
    if not os.path.exists(excel_path):
        return "Excel file not found", 404
        
    try:
        # Load the 'All Results' sheet
        df = pd.read_excel(excel_path, sheet_name='All Results')
        # Regenerate statistics
        stats = generate_stats(df)
        
        # Keep filename for display
        filename = entry['filename']
        
        return render_template('results.html', stats=stats, df=df, user=current_user, filename=filename)
    except Exception as e:
        print(f"Error loading historical analysis: {e}")
        return "Error loading analysis", 500

@app.route('/download')
@app.route('/download/<filename>')
@login_required
def download_file(filename=None):
    if filename:
        # Security check: Does this file belong to the user?
        history = load_history()
        if not any(h['excel_filename'] == filename for h in history):
            return "Access denied", 403
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    else:
        path = os.path.join(app.config['UPLOAD_FOLDER'], f'latest_{current_user.id}.xlsx')
        
    if os.path.exists(path):
        file_type = request.args.get('type')
        download_name = filename if filename else 'result_analysis.xlsx'
        if file_type == 'google':
            download_name = 'ktu_result_google_sheets.xlsx'
        return send_file(path, as_attachment=True, download_name=download_name)
    return "File not found", 404

@app.route('/delete/<entry_id>')
@login_required
def delete_entry(entry_id):
    delete_from_history(entry_id)
    return redirect(url_for('index'))

@app.route('/clear_history')
@login_required
def clear_all_history():
    history = load_history()
    for entry in history:
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], entry['excel_filename'])
        if os.path.exists(excel_path):
            os.remove(excel_path)
    
    # Save an empty list for this user (load_history already filters by user)
    save_history([])
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            
            msg = Message('Password Reset Request',
                          recipients=[email])
            msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
'''
            try:
                # For development, you can print the URL to the console if mail is not configured
                print(f"Reset URL: {reset_url}")
                mail.send(msg)
                flash('An email has been sent with instructions to reset your password.')
            except Exception as e:
                print(f"Error sending email: {e}")
                flash('An email has been sent with instructions to reset your password. (Dev: Check console for link)')
            
            return redirect(url_for('login'))
        else:
            flash('If an account exists with that email, a reset link will be sent.')
            return redirect(url_for('login'))
            
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # 1 hour expiry
    except:
        flash('The reset link is invalid or has expired.')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
            flash('Your password has been updated!')
            return redirect(url_for('login'))
        else:
            flash('User not found.')
            return redirect(url_for('login'))
            
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
