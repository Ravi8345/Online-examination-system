"""Blueprint routes implementing secure authentication, student exams, and administrator CRUD screens."""
from datetime import date
from functools import wraps
from flask import Blueprint, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from extensions import db
from forms import ExamForm, LoginForm, ProfileForm, QuestionForm, RegisterForm, TeacherRegisterForm, SubjectForm
from models import Exam, Question, Result, StudentAnswer, Subject, User
from webcam import get_monitor, release_monitor

main = Blueprint("main", __name__)


def admin_required(view):
    """Restrict a view to authenticated administrator and teacher accounts."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ["Admin", "Teacher"]:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def form_choices(form):
    """Populate dynamic SelectField choices for exam and question forms."""
    if hasattr(form, "subject_id"):
        form.subject_id.choices = [(s.id, s.subject_name) for s in Subject.query.order_by(Subject.subject_name)]
    if hasattr(form, "exam_id"):
        form.exam_id.choices = [(e.id, e.exam_name) for e in Exam.query.order_by(Exam.exam_name)]


@main.route("/")
def home():
    """Render the public landing page."""
    return render_template("home.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    """Register a student with a unique email address and a hashed password."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("That email address is already registered.", "danger")
        else:
            user = User(name=form.name.data, email=form.email.data.lower(), role="Student")
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please sign in.", "success")
            return redirect(url_for("main.login"))
    return render_template("register.html", form=form)


@main.route("/teacher/register", methods=["GET", "POST"])
def teacher_register():
    """Register a teacher with department information and a hashed password."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = TeacherRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("That email address is already registered.", "danger")
        else:
            user = User(
                name=form.name.data,
                email=form.email.data.lower(),
                department=form.department.data,
                role="Teacher"
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Teacher account created. Please sign in with Teacher Login.", "success")
            return redirect(url_for("main.teacher_login"))
    return render_template("auth/teacher_register.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a student through the dedicated student login page."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.role == "Student" and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Invalid student email or password. Teachers should use Teacher Login.", "danger")
    return render_template("login.html", form=form)


@main.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    """Authenticate teacher and administrator accounts for the teacher/admin panel."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.role in ["Teacher", "Admin"] and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("main.admin_dashboard"))
        flash("Invalid teacher email or password.", "danger")
    return render_template("admin/login.html", form=form)


@main.route("/logout")
@login_required
def logout():
    """End the active user session."""
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.home"))


@main.route("/dashboard")
@login_required
def dashboard():
    """Redirect each role to its dedicated dashboard."""
    return redirect(url_for("main.admin_dashboard" if current_user.role == "Admin" else "main.student_dashboard"))


@main.route("/student/dashboard")
@login_required
def student_dashboard():
    """Show a student's available exams and recent outcomes."""
    if current_user.role != "Student": return redirect(url_for("main.admin_dashboard"))
    attempted = {r.exam_id for r in current_user.results}
    available = Exam.query.filter(Exam.exam_date <= date.today()).order_by(Exam.exam_date.desc()).all()
    return render_template("student/dashboard.html", exams=available, attempted=attempted, results=current_user.results)


@main.route("/student/profile", methods=["GET", "POST"])
@login_required
def profile():
    """View and update the current student's display name."""
    if current_user.role != "Student": abort(403)
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("main.profile"))
    return render_template("student/profile.html", form=form)


@main.route("/student/exams")
@login_required
def student_exams():
    """List released exams and whether the student has already attempted each one."""
    if current_user.role != "Student": abort(403)
    attempted = {r.exam_id for r in current_user.results}
    return render_template("student/exams.html", exams=Exam.query.filter(Exam.exam_date <= date.today()).all(), attempted=attempted)


def _exam_or_403(exam_id):
    """Fetch a released exam the current student hasn't already completed, or abort."""
    if current_user.role != "Student": abort(403)
    exam = db.get_or_404(Exam, exam_id)
    if exam.exam_date > date.today(): abort(403)
    if Result.query.filter_by(student_id=current_user.id, exam_id=exam.id).first():
        abort(403)
    return exam


@main.route("/student/exam/<int:exam_id>", methods=["GET", "POST"])
@login_required
def start_exam(exam_id):
    """Render an exam and grade/store one final submission, enforcing one attempt."""
    if current_user.role != "Student": abort(403)
    exam = db.get_or_404(Exam, exam_id)
    if exam.exam_date > date.today(): abort(403)
    if Result.query.filter_by(student_id=current_user.id, exam_id=exam.id).first():
        flash("You have already completed this exam.", "warning")
        return redirect(url_for("main.history"))
    questions = Question.query.filter_by(exam_id=exam.id).all()
    violations_key, verified_key = f"violations_{exam_id}", f"camera_verified_{exam_id}"
    if request.method == "POST":
        score = 0
        for question in questions:
            selected = request.form.get(f"question_{question.id}", "")
            if selected:
                db.session.add(StudentAnswer(student_id=current_user.id, question_id=question.id, selected_option=selected))
            if selected == question.correct_answer:
                score += question.marks
        percentage = round((score / exam.total_marks) * 100, 2) if exam.total_marks else 0
        result = Result(
            student_id=current_user.id, exam_id=exam.id, score=score, percentage=percentage,
            status="Pass" if percentage >= 50 else "Fail",
            camera_verified=bool(session.pop(verified_key, False)),
            face_violations=int(session.pop(violations_key, 0)),
        )
        db.session.add(result)
        db.session.commit()
        release_monitor(current_user.id, exam.id)
        flash("Your exam was submitted.", "success")
        return redirect(url_for("main.result", result_id=result.id))
    session.setdefault(violations_key, 0)
    session[verified_key] = False
    return render_template("student/start_exam.html", exam=exam, questions=questions, max_violations=3)


@main.route("/student/exam/<int:exam_id>/camera/start", methods=["POST"])
@login_required
def camera_start(exam_id):
    """Open the proctoring webcam for this exam attempt."""
    _exam_or_403(exam_id)
    monitor = get_monitor(current_user.id, exam_id)
    ok = monitor.start()
    status = monitor.get_status()
    return jsonify({"ok": ok, "error": status["error"]})


@main.route("/student/exam/<int:exam_id>/camera/feed")
@login_required
def camera_feed(exam_id):
    """Stream the live proctoring webcam as MJPEG for an <img> preview."""
    _exam_or_403(exam_id)
    monitor = get_monitor(current_user.id, exam_id)
    if not monitor.get_status()["active"]:
        abort(404)
    return Response(monitor.frame_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")


@main.route("/student/exam/<int:exam_id>/camera/status")
@login_required
def camera_status(exam_id):
    """Poll the current face-detection status for this exam's webcam."""
    _exam_or_403(exam_id)
    return jsonify(get_monitor(current_user.id, exam_id).get_status())


@main.route("/student/exam/<int:exam_id>/camera/verify", methods=["POST"])
@login_required
def camera_verify(exam_id):
    """Mark that the student confirmed their face is visible before starting."""
    _exam_or_403(exam_id)
    session[f"camera_verified_{exam_id}"] = True
    return jsonify({"ok": True})


@main.route("/student/exam/<int:exam_id>/camera/violation", methods=["POST"])
@login_required
def camera_violation(exam_id):
    """Record one instance of the student's face going missing during the exam."""
    _exam_or_403(exam_id)
    key = f"violations_{exam_id}"
    session[key] = session.get(key, 0) + 1
    return jsonify({"count": session[key]})


@main.route("/student/exam/<int:exam_id>/camera/stop", methods=["POST"])
@login_required
def camera_stop(exam_id):
    """Release the webcam device, e.g. when the student leaves the exam page."""
    if current_user.role != "Student": abort(403)
    release_monitor(current_user.id, exam_id)
    return ("", 204)


@main.route("/student/result/<int:result_id>")
@login_required
def result(result_id):
    """Display a student's own completed result."""
    item = db.get_or_404(Result, result_id)
    if current_user.role != "Admin" and item.student_id != current_user.id: abort(403)
    return render_template("student/result.html", result=item)


@main.route("/student/history")
@login_required
def history():
    """Display all completed examinations for the current student."""
    if current_user.role != "Student": abort(403)
    return render_template("student/history.html", results=Result.query.filter_by(student_id=current_user.id).order_by(Result.submitted_at.desc()).all())


@main.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Display administrator statistics."""
    return render_template("admin/dashboard.html", students=User.query.filter_by(role="Student").count(), subjects=Subject.query.count(), exams=Exam.query.count(), results=Result.query.count())


@main.route("/admin/subjects", methods=["GET", "POST"])
@login_required
@admin_required
def subjects():
    """Create and list subjects."""
    form = SubjectForm()
    if form.validate_on_submit():
        if Subject.query.filter_by(subject_name=form.subject_name.data).first(): flash("Subject already exists.", "danger")
        else:
            db.session.add(Subject(subject_name=form.subject_name.data)); db.session.commit(); flash("Subject saved.", "success")
        return redirect(url_for("main.subjects"))
    return render_template("admin/subjects.html", form=form, subjects=Subject.query.order_by(Subject.subject_name).all())


@main.route("/admin/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_subject(subject_id):
    """Delete a subject and its dependent exams after CSRF-protected form submission."""
    db.session.delete(db.get_or_404(Subject, subject_id)); db.session.commit(); flash("Subject deleted.", "success")
    return redirect(url_for("main.subjects"))


@main.route("/admin/exams", methods=["GET", "POST"])
@login_required
@admin_required
def admin_exams():
    """Publish and list examinations for students."""
    form = ExamForm(); form_choices(form)
    if form.validate_on_submit():
        db.session.add(Exam(subject_id=form.subject_id.data, exam_name=form.exam_name.data, duration=form.duration.data, total_marks=form.total_marks.data, exam_date=form.exam_date.data)); db.session.commit(); flash("Exam saved.", "success")
        return redirect(url_for("main.admin_exams"))
    return render_template("admin/exams.html", form=form, exams=Exam.query.order_by(Exam.exam_date.desc()).all(), has_subjects=Subject.query.count() > 0)


@main.route("/admin/exams/<int:exam_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_exam(exam_id):
    """Delete an exam and its dependent questions/results."""
    db.session.delete(db.get_or_404(Exam, exam_id)); db.session.commit(); flash("Exam deleted.", "success")
    return redirect(url_for("main.admin_exams"))


@main.route("/admin/questions", methods=["GET", "POST"])
@login_required
@admin_required
def questions():
    """Add questions to published examinations."""
    form = QuestionForm(); form_choices(form)
    if form.validate_on_submit():
        db.session.add(Question(exam_id=form.exam_id.data, question=form.question.data, option_a=form.option_a.data, option_b=form.option_b.data, option_c=form.option_c.data, option_d=form.option_d.data, correct_answer=form.correct_answer.data, marks=form.marks.data)); db.session.commit(); flash("Question saved.", "success")
        return redirect(url_for("main.questions"))
    return render_template("admin/questions.html", form=form, questions=Question.query.order_by(Question.id.desc()).all(), has_exams=Exam.query.count() > 0)


@main.route("/admin/questions/<int:question_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_question(question_id):
    """Delete a single question."""
    db.session.delete(db.get_or_404(Question, question_id)); db.session.commit(); flash("Question deleted.", "success")
    return redirect(url_for("main.questions"))


@main.route("/admin/students")
@login_required
@admin_required
def students():
    """List students with a safe SQLAlchemy search filter."""
    query = request.args.get("q", "").strip()
    student_query = User.query.filter_by(role="Student")
    if query: student_query = student_query.filter((User.name.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")))
    return render_template("admin/students.html", students=student_query.order_by(User.name).all(), query=query)


@main.route("/admin/results")
@login_required
@admin_required
def admin_results():
    """List results, optionally filtered by pass/fail status."""
    status = request.args.get("status", "")
    query = Result.query
    if status in ("Pass", "Fail"): query = query.filter_by(status=status)
    return render_template("admin/results.html", results=query.order_by(Result.submitted_at.desc()).all(), status=status)


@main.route("/admin/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_subject(subject_id):
    """Edit an existing subject."""
    subject = db.get_or_404(Subject, subject_id); form = SubjectForm(obj=subject)
    if form.validate_on_submit():
        subject.subject_name = form.subject_name.data; db.session.commit(); flash("Subject updated.", "success")
        return redirect(url_for("main.subjects"))
    return render_template("admin/subjects.html", form=form, subjects=Subject.query.order_by(Subject.subject_name).all(), editing=subject)


@main.route("/admin/exams/<int:exam_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_exam(exam_id):
    """Edit an existing examination."""
    exam = db.get_or_404(Exam, exam_id); form = ExamForm(obj=exam); form_choices(form)
    if form.validate_on_submit():
        for field in ("subject_id", "exam_name", "duration", "total_marks", "exam_date"): setattr(exam, field, getattr(form, field).data)
        db.session.commit(); flash("Exam updated.", "success"); return redirect(url_for("main.admin_exams"))
    return render_template("admin/exams.html", form=form, exams=Exam.query.order_by(Exam.exam_date.desc()).all(), editing=exam, has_subjects=True)


@main.route("/admin/questions/<int:question_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_question(question_id):
    """Edit an existing multiple-choice question."""
    item = db.get_or_404(Question, question_id); form = QuestionForm(obj=item); form_choices(form)
    if form.validate_on_submit():
        for field in ("exam_id", "question", "option_a", "option_b", "option_c", "option_d", "correct_answer", "marks"): setattr(item, field, getattr(form, field).data)
        db.session.commit(); flash("Question updated.", "success"); return redirect(url_for("main.questions"))
    return render_template("admin/questions.html", form=form, questions=Question.query.order_by(Question.id.desc()).all(), editing=item, has_exams=True)
