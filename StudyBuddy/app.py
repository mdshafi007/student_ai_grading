import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

from models import db, User, Assignment, Feedback
from ai_client import AIGradingClient
from file_utils import allowed_file, extract_text_from_file, save_uploaded_file, UPLOAD_FOLDER

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grading_assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize AI client
ai_client = AIGradingClient()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Security error. Please try again.', 'error')
    return redirect(request.referrer or url_for('index')), 400

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('teacher_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('teacher_dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('teacher_dashboard'))
    
    assignments = Assignment.query.filter_by(student_id=current_user.id).order_by(Assignment.uploaded_at.desc()).all()
    return render_template('dashboard_student.html', assignments=assignments)

@app.route('/student/upload', methods=['GET', 'POST'])
@login_required
def upload_assignment():
    if current_user.role != 'student':
        return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Save file
                filepath, filename = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
                
                # Extract text content
                text_content = extract_text_from_file(filepath, filename)
                
                # Save assignment to database
                assignment = Assignment(
                    student_id=current_user.id,
                    filename=filename,
                    filepath=filepath,
                    text_content=text_content
                )
                db.session.add(assignment)
                db.session.commit()
                
                flash('Assignment uploaded successfully!', 'success')
                return redirect(url_for('student_dashboard'))
                
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'error')
        else:
            flash('Invalid file type. Please upload PDF, DOCX, or TXT files only.', 'error')
    
    return render_template('upload.html')

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        return redirect(url_for('student_dashboard'))
    
    assignments = Assignment.query.join(User).order_by(Assignment.uploaded_at.desc()).all()
    return render_template('dashboard_teacher.html', assignments=assignments)

@app.route('/teacher/assignments')
@login_required
def assignment_list():
    if current_user.role != 'teacher':
        return redirect(url_for('student_dashboard'))
    
    assignments = Assignment.query.join(User).order_by(Assignment.uploaded_at.desc()).all()
    return render_template('assignment_list.html', assignments=assignments)

@app.route('/assignment/<int:assignment_id>')
@login_required
def view_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Students can only view their own assignments
    if current_user.role == 'student' and assignment.student_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('student_dashboard'))
    
    feedbacks = Feedback.query.filter_by(assignment_id=assignment_id).order_by(Feedback.created_at.desc()).all()
    return render_template('view_assignment.html', assignment=assignment, feedbacks=feedbacks)

@app.route('/generate_feedback/<int:assignment_id>', methods=['POST'])
@login_required
def generate_feedback(assignment_id):
    if current_user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('student_dashboard'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    try:
        # Generate feedback using AI
        result = ai_client.generate_feedback(assignment.text_content, assignment.filename)
        
        # Save feedback to database
        feedback = Feedback(
            assignment_id=assignment_id,
            teacher_id=current_user.id,
            content=result['feedback'],
            score=result['score'],
            generated_by_ai=True
        )
        db.session.add(feedback)
        db.session.commit()
        
        flash('Feedback generated successfully!', 'success')
        
    except Exception as e:
        flash(f'Error generating feedback: {str(e)}', 'error')
    
    return redirect(url_for('view_assignment', assignment_id=assignment_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)