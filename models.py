class User:
    def __init__(self, id, name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row['id'],
            name=row['name'],
            email=row['email'],
            role=row['role']
        )


class Course:
    def __init__(self, id, name, subject, teacher_id):
        self.id = id
        self.name = name
        self.subject = subject
        self.teacher_id = teacher_id
    
    def get_materials(self, db):
        return db.get_materials_by_course(self.id)
    
    def get_assignments(self, db):
        return db.get_assignments_by_course(self.id)
    
    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row['id'],
            name=row['name'],
            subject=row['subject'],
            teacher_id=row['teacher_id']
        )


class Submission:
    def __init__(self, id, assignment_id, student_id, filename, score):
        self.id = id
        self.assignment_id = assignment_id
        self.student_id = student_id
        self.filename = filename
        self.score = score
    
    def is_graded(self):
        return self.score is not None
    
    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row['id'],
            assignment_id=row['assignment_id'],
            student_id=row['student_id'],
            filename=row['filename'],
            score=row['score']
        )
