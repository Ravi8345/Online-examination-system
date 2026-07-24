"""Flask-WTF forms with server-side validation for authentication and administrator management."""
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange


class RegisterForm(FlaskForm):
    """Student account registration form."""
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create account")


class TeacherRegisterForm(FlaskForm):
    """Teacher account registration form."""
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    department = StringField("Department", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create teacher account")


class LoginForm(FlaskForm):
    """Login form shared by administrators and students."""
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class SubjectForm(FlaskForm):
    """Subject create and edit form."""
    subject_name = StringField("Subject name", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Save subject")


class ExamForm(FlaskForm):
    """Exam create and edit form."""
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    exam_name = StringField("Exam name", validators=[DataRequired(), Length(max=160)])
    duration = IntegerField("Duration (minutes)", validators=[DataRequired(), NumberRange(min=1)])
    total_marks = IntegerField("Total marks", validators=[DataRequired(), NumberRange(min=1)])
    exam_date = DateField("Exam date", validators=[DataRequired()])
    submit = SubmitField("Save exam")


class QuestionForm(FlaskForm):
    """Multiple-choice question create and edit form."""
    exam_id = SelectField("Exam", coerce=int, validators=[DataRequired()])
    question = TextAreaField("Question", validators=[DataRequired()])
    option_a = StringField("Option A", validators=[DataRequired()])
    option_b = StringField("Option B", validators=[DataRequired()])
    option_c = StringField("Option C", validators=[DataRequired()])
    option_d = StringField("Option D", validators=[DataRequired()])
    correct_answer = SelectField("Correct answer", choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")], validators=[DataRequired()])
    marks = IntegerField("Marks", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Save question")


class ProfileForm(FlaskForm):
    """Student self-service profile form."""
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Update profile")
