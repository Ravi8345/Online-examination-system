"""SQLAlchemy ORM models for users, examinations, responses, and calculated results."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db, login_manager


class User(UserMixin, db.Model):
    """Account for an administrator, teacher, or student."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="Student")
    department = db.Column(db.String(120), nullable=True)  # For teachers
    answers = db.relationship("StudentAnswer", backref="student", lazy=True, cascade="all, delete-orphan")
    results = db.relationship("Result", backref="student", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Securely hash and store a plain-text password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Return whether a submitted password matches the stored hash."""
        return check_password_hash(self.password, password)


@login_manager.user_loader
def load_user(user_id):
    """Restore a logged-in user from Flask-Login's session identifier."""
    return db.session.get(User, int(user_id))


class Subject(db.Model):
    """Academic subject that groups examinations."""
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(120), unique=True, nullable=False)
    exams = db.relationship("Exam", backref="subject", lazy=True, cascade="all, delete-orphan")


class Exam(db.Model):
    """Timed examination created under a subject."""
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    exam_name = db.Column(db.String(160), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    questions = db.relationship("Question", backref="exam", lazy=True, cascade="all, delete-orphan")
    results = db.relationship("Result", backref="exam", lazy=True, cascade="all, delete-orphan")


class Question(db.Model):
    """Multiple-choice question with one correct option letter."""
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    marks = db.Column(db.Integer, nullable=False, default=1)
    answers = db.relationship("StudentAnswer", backref="question_item", lazy=True, cascade="all, delete-orphan")


class StudentAnswer(db.Model):
    """A student's selected answer to a question in a completed exam."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    selected_option = db.Column(db.String(1), nullable=False)


class Result(db.Model):
    """Final score and outcome for one student examination attempt."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    camera_verified = db.Column(db.Boolean, nullable=False, default=False)
    face_violations = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (db.UniqueConstraint("student_id", "exam_id", name="uq_student_exam_attempt"),)
