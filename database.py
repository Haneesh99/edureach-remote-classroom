import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='edureach.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('teacher', 'student'))
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                teacher_id INTEGER NOT NULL,
                description TEXT,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (course_id) REFERENCES courses(id),
                UNIQUE(student_id, course_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                upload_path TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                deadline DATE,
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                filename TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                score REAL,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                date DATE NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('present', 'absent')),
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                UNIQUE(course_id, student_id, date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option TEXT NOT NULL CHECK(correct_option IN ('a', 'b', 'c', 'd')),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, name, email, password_hash, role):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
            (name, email, password_hash, role)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def get_user_by_email(self, email):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_teachers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE role = ?', ('teacher',))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def create_course(self, name, subject, teacher_id, description=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO courses (name, subject, teacher_id, description) VALUES (?, ?, ?, ?)',
            (name, subject, teacher_id, description)
        )
        course_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return course_id
    
    def get_course_by_id(self, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_courses_by_teacher(self, teacher_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM courses WHERE teacher_id = ?', (teacher_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_all_courses(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM courses')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_courses_by_student(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.* FROM courses c
            JOIN enrollments e ON c.id = e.course_id
            WHERE e.student_id = ?
        ''', (student_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def enroll_student(self, student_id, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)',
                (student_id, course_id)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def get_enrolled_students(self, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.* FROM users u
            JOIN enrollments e ON u.id = e.student_id
            WHERE e.course_id = ?
        ''', (course_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def is_enrolled(self, student_id, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM enrollments WHERE student_id = ? AND course_id = ?',
            (student_id, course_id)
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None
    
    def add_material(self, course_id, filename, upload_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO materials (course_id, filename, upload_path) VALUES (?, ?, ?)',
            (course_id, filename, upload_path)
        )
        material_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return material_id
    
    def get_materials_by_course(self, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM materials WHERE course_id = ? ORDER BY uploaded_at DESC', (course_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def create_assignment(self, course_id, title, description, deadline):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO assignments (course_id, title, description, deadline) VALUES (?, ?, ?, ?)',
            (course_id, title, description, deadline)
        )
        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return assignment_id
    
    def get_assignments_by_course(self, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM assignments WHERE course_id = ? ORDER BY deadline', (course_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_assignment_by_id(self, assignment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM assignments WHERE id = ?', (assignment_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def submit_assignment(self, assignment_id, student_id, filename):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO submissions (assignment_id, student_id, filename) VALUES (?, ?, ?)',
            (assignment_id, student_id, filename)
        )
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return submission_id
    
    def get_submissions_by_assignment(self, assignment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM submissions WHERE assignment_id = ? ORDER BY submitted_at DESC',
            (assignment_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_submissions_by_student(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM submissions WHERE student_id = ? ORDER BY submitted_at DESC',
            (student_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def grade_submission(self, submission_id, score):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE submissions SET score = ? WHERE id = ?', (score, submission_id))
        conn.commit()
        conn.close()
    
    def mark_attendance(self, course_id, student_id, date, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO attendance (course_id, student_id, date, status) VALUES (?, ?, ?, ?)',
                (course_id, student_id, date, status)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            cursor.execute(
                'UPDATE attendance SET status = ? WHERE course_id = ? AND student_id = ? AND date = ?',
                (status, course_id, student_id, date)
            )
            conn.commit()
            conn.close()
            return True
    
    def get_attendance_by_course(self, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM attendance WHERE course_id = ? ORDER BY date DESC',
            (course_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_attendance_by_student(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC',
            (student_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_attendance_for_student_in_course(self, student_id, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM attendance WHERE student_id = ? AND course_id = ?',
            (student_id, course_id)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def create_announcement(self, course_id, message):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO announcements (course_id, message) VALUES (?, ?)',
            (course_id, message)
        )
        announcement_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return announcement_id
    
    def get_announcements_by_course(self, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM announcements WHERE course_id = ? ORDER BY posted_at DESC',
            (course_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def add_quiz_question(self, course_id, question, option_a, option_b, option_c, option_d, correct_option):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO quiz_questions 
               (course_id, question, option_a, option_b, option_c, option_d, correct_option) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (course_id, question, option_a, option_b, option_c, option_d, correct_option)
        )
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return question_id
    
    def get_quiz_questions_by_course(self, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM quiz_questions WHERE course_id = ?',
            (course_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def save_quiz_result(self, student_id, course_id, score, total):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO quiz_results (student_id, course_id, score, total) VALUES (?, ?, ?, ?)',
            (student_id, course_id, score, total)
        )
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return result_id
    
    def get_quiz_results_by_student(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM quiz_results WHERE student_id = ? ORDER BY taken_at DESC',
            (student_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_quiz_results_by_student_and_course(self, student_id, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM quiz_results WHERE student_id = ? AND course_id = ? ORDER BY taken_at DESC',
            (student_id, course_id)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def record_login(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO login_history (user_id) VALUES (?)', (user_id,))
        conn.commit()
        conn.close()
    
    def has_logged_in(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM login_history WHERE user_id = ? LIMIT 1', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    
    def has_submitted_assignment(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM submissions WHERE student_id = ? LIMIT 1', (student_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    
    def has_perfect_quiz(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM quiz_results WHERE student_id = ? AND score = total LIMIT 1',
            (student_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None
    
    def has_full_attendance(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) as total FROM attendance WHERE student_id = ?',
            (student_id,)
        )
        total = cursor.fetchone()['total']
        cursor.execute(
            'SELECT COUNT(*) as present FROM attendance WHERE student_id = ? AND status = ?',
            (student_id, 'present')
        )
        present = cursor.fetchone()['present']
        conn.close()
        return total > 0 and total == present
    
    def get_average_score(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT AVG(CAST(score AS FLOAT) / total * 100) as avg_score FROM quiz_results WHERE student_id = ?',
            (student_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row['avg_score'] if row['avg_score'] else 0

    def get_all_students_with_scores(self, course_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.name, AVG(CAST(qr.score AS FLOAT) / qr.total * 100) as avg_score
            FROM users u
            JOIN quiz_results qr ON u.id = qr.student_id
            WHERE qr.course_id = ? AND u.role = 'student'
            GROUP BY u.id
        ''', (course_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
