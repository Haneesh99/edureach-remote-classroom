import os
import functools
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database import Database
from models import User, Course, Submission
from lang import get_text, DEFAULT_LANG, get_available_languages
from badges import compute_badges, get_badge_details
from recommendations import get_recommendation

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'edureach-dev-secret-key-change-in-production')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'png', 'jpg', 'jpeg', 'zip'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = Database()

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Custom login_required decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        user_id = g.get('user_id')
        if user_id is None:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view


# Load logged-in user before each request
@app.before_request
def load_logged_in_user():
    g.user_id = None
    g.user = None
    g.lang = request.cookies.get('lang', DEFAULT_LANG)
    
    if 'user_id' in request.cookies:
        try:
            user_id = int(request.cookies.get('user_id'))
            user_data = db.get_user_by_id(user_id)
            if user_data:
                g.user_id = user_id
                g.user = User.from_db_row(user_data)
        except (ValueError, TypeError):
            pass


# Template globals
@app.context_processor
def inject_globals():
    return {
        'get_text': lambda key: get_text(key, g.get('lang', DEFAULT_LANG)),
        'get_badge_details': get_badge_details,
        'lang': g.get('lang', DEFAULT_LANG)
    }


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Routes
@app.route('/')
def index():
    if g.user:
        if g.user.is_teacher():
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        user_data = db.get_user_by_email(email)
        if user_data and check_password_hash(user_data['password_hash'], password):
            db.record_login(user_data['id'])
            response = redirect(url_for('teacher_dashboard' if user_data['role'] == 'teacher' else 'student_dashboard'))
            response.set_cookie('user_id', str(user_data['id']), max_age=60*60*24*7)
            flash('Login successful!', 'success')
            return response
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        
        if not name or not email or not password or not role:
            flash('All fields are required.', 'error')
            return render_template('signup.html')
        
        if role not in ('teacher', 'student'):
            flash('Invalid role selected.', 'error')
            return render_template('signup.html')
        
        if db.get_user_by_email(email):
            flash('Email already exists. Please use a different email.', 'error')
            return render_template('signup.html')
        
        password_hash = generate_password_hash(password)
        user_id = db.create_user(name, email, password_hash, role)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


@app.route('/logout')
def logout():
    response = redirect(url_for('index'))
    response.delete_cookie('user_id')
    flash('You have been logged out.', 'success')
    return response


@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if not g.user.is_teacher():
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))
    
    courses_data = db.get_courses_by_teacher(g.user_id)
    courses = []
    total_students = 0
    total_materials = 0
    flagged_students = []
    
    for course_data in courses_data:
        course = Course.from_db_row(course_data)
        students = db.get_enrolled_students(course.id)
        materials = course.get_materials(db)
        
        total_students += len(students)
        total_materials += len(materials)
        
        # Check for flagged students based on quiz scores
        student_scores = db.get_all_students_with_scores(course.id)
        for student_score in student_scores:
            if student_score['avg_score'] < 60:
                flagged_students.append({
                    'name': student_score['name'],
                    'course': course.name,
                    'score': round(student_score['avg_score'], 1),
                    'reason': f"Low quiz performance ({round(student_score['avg_score'], 1)}%)"
                })
        
        courses.append({
            'id': course.id,
            'name': course.name,
            'subject': course.subject,
            'description': course_data.get('description', ''),
            'student_count': len(students)
        })
    
    return render_template('teacher_dashboard.html',
                         user=g.user,
                         courses=courses,
                         total_students=total_students,
                         total_materials=total_materials,
                         flagged_students=flagged_students)


@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if not g.user.is_student():
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    enrolled_courses_data = db.get_courses_by_student(g.user_id)
    enrolled_courses = [dict(course) for course in enrolled_courses_data]
    
    all_courses_data = db.get_all_courses()
    available_courses = [
        dict(course) for course in all_courses_data 
        if not db.is_enrolled(g.user_id, course['id'])
    ]
    
    # Calculate attendance rate
    attendance_records = db.get_attendance_by_student(g.user_id)
    if attendance_records:
        present_count = len([a for a in attendance_records if a['status'] == 'present'])
        attendance_rate = round((present_count / len(attendance_records)) * 100)
    else:
        attendance_rate = 0
    
    # Get badges
    badges = compute_badges(g.user_id, db)
    
    # Get recommendations from recent quiz results
    recommendations = []
    quiz_results = db.get_quiz_results_by_student(g.user_id)
    seen_courses = set()
    
    level_class_map = {
        "Struggling": "struggling",
        "Needs Practice": "needs-practice",
        "On Track": "on-track",
        "Excellent": "excellent"
    }
    
    for result in quiz_results:
        if result['course_id'] not in seen_courses and len(recommendations) < 3:
            seen_courses.add(result['course_id'])
            percentage = (result['score'] / result['total']) * 100
            course = db.get_course_by_id(result['course_id'])
            if course:
                rec = get_recommendation(percentage, course['name'])
                recommendations.append({
                    'level': rec['level'],
                    'level_class': level_class_map.get(rec['level'], ''),
                    'message': rec['message']
                })
    
    return render_template('student_dashboard.html',
                         user=g.user,
                         enrolled_courses=enrolled_courses,
                         available_courses=available_courses,
                         attendance_rate=attendance_rate,
                         badges=badges,
                         recommendations=recommendations)


@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    course = db.get_course_by_id(course_id)
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('index'))
    
    materials = db.get_materials_by_course(course_id)
    assignments = db.get_assignments_by_course(course_id)
    announcements = db.get_announcements_by_course(course_id)
    teacher = db.get_user_by_id(course['teacher_id'])
    students = db.get_enrolled_students(course_id)
    quiz_questions = db.get_quiz_questions_by_course(course_id)
    
    # Check if student has submitted each assignment
    submitted_assignments = set()
    if g.user.is_student():
        for assignment in assignments:
            submissions = db.get_submissions_by_assignment(assignment['id'])
            for sub in submissions:
                if sub['student_id'] == g.user_id:
                    submitted_assignments.add(assignment['id'])
                    break
    
    return render_template('course.html',
                         user=g.user,
                         course=course,
                         materials=materials,
                         assignments=assignments,
                         announcements=announcements,
                         teacher=teacher,
                         students=students,
                         quiz_questions=quiz_questions,
                         submitted_assignments=submitted_assignments,
                         today=date.today().isoformat())


@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    if not g.user.is_student():
        flash('Only students can enroll in courses.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    if db.enroll_student(g.user_id, course_id):
        flash('Successfully enrolled in course!', 'success')
    else:
        flash('Already enrolled in this course.', 'warning')
    
    return redirect(url_for('student_dashboard'))


@app.route('/create_course', methods=['POST'])
@login_required
def create_course():
    if not g.user.is_teacher():
        flash('Only teachers can create courses.', 'error')
        return redirect(url_for('index'))
    
    name = request.form.get('course_name', '').strip()
    subject = request.form.get('subject', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name or not subject:
        flash('Course name and subject are required.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    db.create_course(name, subject, g.user_id, description)
    flash('Course created successfully!', 'success')
    return redirect(url_for('teacher_dashboard'))


@app.route('/upload_material/<int:course_id>', methods=['POST'])
@login_required
def upload_material(course_id):
    if not g.user.is_teacher():
        flash('Only teachers can upload materials.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    course = db.get_course_by_id(course_id)
    if not course or course['teacher_id'] != g.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to filename to avoid collisions
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        db.add_material(course_id, filename, upload_path)
        flash('Material uploaded successfully!', 'success')
    else:
        flash('Invalid file type.', 'error')
    
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/download/<path:filename>')
@login_required
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/create_assignment/<int:course_id>', methods=['POST'])
@login_required
def create_assignment_route(course_id):
    if not g.user.is_teacher():
        flash('Only teachers can create assignments.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    course = db.get_course_by_id(course_id)
    if not course or course['teacher_id'] != g.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    deadline = request.form.get('deadline', '').strip()
    
    if not title or not deadline:
        flash('Title and deadline are required.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    db.create_assignment(course_id, title, description, deadline)
    flash('Assignment created successfully!', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/submit_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    if not g.user.is_student():
        flash('Only students can submit assignments.', 'error')
        return redirect(url_for('index'))
    
    assignment = db.get_assignment_by_id(assignment_id)
    if not assignment:
        flash('Assignment not found.', 'error')
        return redirect(url_for('student_dashboard'))
    
    if not db.is_enrolled(g.user_id, assignment['course_id']):
        flash('You must be enrolled in the course to submit assignments.', 'error')
        return redirect(url_for('student_dashboard'))
    
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('course_detail', course_id=assignment['course_id']))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('course_detail', course_id=assignment['course_id']))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"submission_{g.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        db.submit_assignment(assignment_id, g.user_id, filename)
        flash('Assignment submitted successfully!', 'success')
    else:
        flash('Invalid file type.', 'error')
    
    return redirect(url_for('course_detail', course_id=assignment['course_id']))


@app.route('/mark_attendance/<int:course_id>', methods=['POST'])
@login_required
def mark_attendance(course_id):
    if not g.user.is_teacher():
        flash('Only teachers can mark attendance.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    course = db.get_course_by_id(course_id)
    if not course or course['teacher_id'] != g.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    attendance_date = request.form.get('date', date.today().isoformat())
    students = db.get_enrolled_students(course_id)
    
    for student in students:
        status = request.form.get(f'student_{student["id"]}', '')
        if status in ('present', 'absent'):
            db.mark_attendance(course_id, student['id'], attendance_date, status)
    
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/announcement/<int:course_id>', methods=['POST'])
@login_required
def post_announcement(course_id):
    if not g.user.is_teacher():
        flash('Only teachers can post announcements.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    course = db.get_course_by_id(course_id)
    if not course or course['teacher_id'] != g.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    message = request.form.get('message', '').strip()
    if not message:
        flash('Message is required.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    db.create_announcement(course_id, message)
    flash('Announcement posted successfully!', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/create_quiz/<int:course_id>', methods=['POST'])
@login_required
def create_quiz(course_id):
    if not g.user.is_teacher():
        flash('Only teachers can create quizzes.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    course = db.get_course_by_id(course_id)
    if not course or course['teacher_id'] != g.user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    question = request.form.get('question', '').strip()
    option_a = request.form.get('option_a', '').strip()
    option_b = request.form.get('option_b', '').strip()
    option_c = request.form.get('option_c', '').strip()
    option_d = request.form.get('option_d', '').strip()
    correct_option = request.form.get('correct_option', '').strip()
    
    if not all([question, option_a, option_b, option_c, option_d, correct_option]):
        flash('All fields are required to create a quiz question.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    if correct_option not in ('a', 'b', 'c', 'd'):
        flash('Correct option must be a, b, c, or d.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    db.add_quiz_question(course_id, question, option_a, option_b, option_c, option_d, correct_option)
    flash('Quiz question added successfully!', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/quiz/delete/<int:question_id>', methods=['POST'])
@login_required
def delete_quiz(question_id):
    if not g.user.is_teacher():
        flash('Only teachers can delete quiz questions.', 'error')
        return redirect(url_for('index'))
    
    # Get the question to find its course
    question = db.get_quiz_question_by_id(question_id)
    if not question:
        flash('Question not found.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Verify the teacher owns the course
    course = db.get_course_by_id(question['course_id'])
    if not course or course['teacher_id'] != g.user_id:
        flash('Access denied. You can only delete questions from your own courses.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Delete the question
    db.delete_quiz_question(question_id)
    flash('Quiz question deleted successfully!', 'success')
    return redirect(url_for('course_detail', course_id=question['course_id']))


@app.route('/quiz/<int:course_id>')
@login_required
def quiz(course_id):
    if not g.user.is_student():
        flash('Only students can take quizzes.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    if not db.is_enrolled(g.user_id, course_id):
        flash('You must be enrolled in the course to take the quiz.', 'error')
        return redirect(url_for('student_dashboard'))
    
    course = db.get_course_by_id(course_id)
    questions = db.get_quiz_questions_by_course(course_id)
    
    # Check if already taken recently
    previous_results = db.get_quiz_results_by_student_and_course(g.user_id, course_id)
    result = None
    if previous_results:
        # Show the most recent result
        last_result = previous_results[0]
        percentage = (last_result['score'] / last_result['total']) * 100
        course_name = course['name']
        recommendation = get_recommendation(percentage, course_name)
        result = {
            'score': last_result['score'],
            'total': last_result['total'],
            'percentage': round(percentage, 1),
            'recommendation': recommendation
        }
    
    return render_template('quiz.html',
                         user=g.user,
                         course=course,
                         questions=questions,
                         result=result)


@app.route('/quiz/submit/<int:course_id>', methods=['POST'])
@login_required
def submit_quiz(course_id):
    if not g.user.is_student():
        flash('Only students can submit quizzes.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    if not db.is_enrolled(g.user_id, course_id):
        flash('You must be enrolled in the course.', 'error')
        return redirect(url_for('student_dashboard'))
    
    questions = db.get_quiz_questions_by_course(course_id)
    
    score = 0
    total = len(questions)
    
    for question in questions:
        answer = request.form.get(f'q{question["id"]}', '')
        if answer == question['correct_option']:
            score += 1
    
    db.save_quiz_result(g.user_id, course_id, score, total)
    
    percentage = (score / total) * 100 if total > 0 else 0
    course = db.get_course_by_id(course_id)
    recommendation = get_recommendation(percentage, course['name'])
    
    flash(f'Quiz completed! Score: {score}/{total} ({round(percentage, 1)}%)', 'success')
    return redirect(url_for('quiz', course_id=course_id))


# Sample data initialization
def init_sample_data():
    """Initialize sample data for testing."""
    # Check if any users exist
    teachers = db.get_all_teachers()
    
    if not teachers:
        # Create sample teacher
        teacher_id = db.create_user(
            'Dr. Rajesh Kumar',
            'teacher@edureach.com',
            generate_password_hash('teacher123'),
            'teacher'
        )
        
        # Create sample course
        course_id = db.create_course(
            'Introduction to Python Programming',
            'Computer Science',
            teacher_id,
            'A beginner-friendly course covering Python basics, data structures, and object-oriented programming.'
        )
        
        # Create sample quiz questions
        db.add_quiz_question(course_id, 
            'What is the output of print(2 + 3)?',
            '23', '5', '2+3', 'None', 'b')
        db.add_quiz_question(course_id,
            'Which of the following is used to define a function in Python?',
            'function', 'def', 'func', 'define', 'b')
        db.add_quiz_question(course_id,
            'What is the correct way to create a list in Python?',
            'list = ()', 'list = []', 'list = {}', 'list = ""', 'b')
        db.add_quiz_question(course_id,
            'Which operator is used for exponentiation in Python?',
            '^', '**', '*', '//', 'b')
        db.add_quiz_question(course_id,
            'What does the len() function do?',
            'Returns the length of an object', 'Creates a new list', 'Converts to string', 'Sorts the list', 'a')
        
        # Create sample assignment
        db.create_assignment(
            course_id,
            'Python Basics Assignment',
            'Write a Python program to calculate the factorial of a number.',
            '2026-12-31'
        )
    
    # Create sample student if none exist
    if not db.get_user_by_email('student@edureach.com'):
        student_id = db.create_user(
            'Priya Sharma',
            'student@edureach.com',
            generate_password_hash('student123'),
            'student'
        )
        
        # Enroll in the first available course
        courses = db.get_all_courses()
        if courses:
            db.enroll_student(student_id, courses[0]['id'])


if __name__ == '__main__':
    init_sample_data()
    app.run(debug=True, host='0.0.0.0', port=5000)
