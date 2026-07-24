# Online Examination System

A complete Flask/MySQL examination portal with secure login, student exam delivery, automatic grading, and administrator management screens.

## Features

- Student registration, secure password hashing, Flask-Login sessions, and CSRF-protected forms.
- Administrator and student dashboards with role-based access control.
- Subject, exam, and question create, edit, and delete workflows.
- Timed multiple-choice exams, one attempt per student, answer storage, score calculation, and pass/fail results.
- Student search and result filtering.

## Project tree

```text
app.py                 Application factory and entry point
config.py              Environment-based Flask/MySQL configuration
extensions.py          Flask extension instances
models.py              SQLAlchemy database models
forms.py               Validated Flask-WTF forms
routes.py              Blueprint routes and authorization checks
schema.sql             Standalone MySQL schema
templates/             Jinja2 pages for public, student, and admin areas
static/css/style.css   Responsive CSS design system
```

## Setup (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY = "replace-with-a-long-random-value"
python app.py
```

Open `http://127.0.0.1:5000` in a browser. The application uses a local SQLite database by default, so no MySQL server is required for development.

### Use XAMPP / MySQL instead of SQLite
1. Start XAMPP and start the MySQL service.
2. Open phpMyAdmin or run the MySQL shell and create the database:

```sql
CREATE DATABASE `online-exam` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. In PowerShell set the environment variable before launching the app. You can use a MySQL user ID like `mysqlid`:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-value"
$env:MYSQL_USER = "mysqlid"
$env:MYSQL_PASSWORD = "YOUR_PASSWORD"
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_DATABASE = "online-exam"
python app.py
```

If you prefer one URL instead, set `DATABASE_URL` directly:

```powershell
$env:DATABASE_URL = "mysql+pymysql://mysqlid:YOUR_PASSWORD@127.0.0.1/online-exam"
python app.py
```

If your XAMPP root user has no password, use:

```powershell
$env:DATABASE_URL = "mysql+pymysql://root:@127.0.0.1/online-exam"
```

The application will connect to the XAMPP MySQL database and SQLAlchemy will create the database tables automatically on first startup.

If you prefer to create tables manually, import `schema.sql` into the `online-exam` database from phpMyAdmin or the MySQL shell.

## First administrator

Create the administrator from the command line—public registration deliberately creates **Student** accounts only:

```powershell
.\venv\Scripts\Activate.ps1
flask --app app:create_app create-admin
```

Enter the prompted name, email, and password. Then sign in through `/login`; the navigation will show **Admin dashboard** and **Manage**. Running the command with an existing email safely promotes that account to Administrator.

## Test checklist

1. Register a student and confirm duplicate email registration is rejected.
2. Promote one account to Admin, create a subject, an exam, and questions.
3. Log in as a student, complete the released exam, and verify the result/history.
4. Confirm a second submission is blocked and admin results can be filtered.
