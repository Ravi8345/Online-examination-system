# 🎓 AI-Powered Online Examination System

A secure and intelligent **Online Examination System** developed using **Python Flask**, **MySQL**, and **OpenCV**. The application provides a complete platform for conducting online examinations with role-based access for **Admin**, **Teacher**, and **Student**, while enhancing exam integrity through webcam-based face detection.



# 🚀 Features

* 🔐 Secure user authentication
* 👨‍💼 Admin, Teacher, and Student dashboards
* 📚 Subject and Exam Management
* ❓ Question Bank Management
* 📝 Online Examination Portal
* 📊 Automatic Result Generation
* 📸 Webcam-based Face Detection using OpenCV
* 🛡️ CSRF Protection
* 🔑 Session Management with Flask-Login
* 💾 MySQL Database Integration
* 📱 Responsive User Interface

# 🛠️ Technologies Used

## Backend

* Python
* Flask
* Flask-SQLAlchemy
* Flask-Login
* Flask-WTF
* OpenCV

## Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap

## Database

* MySQL

## Tools

* Visual Studio Code
* XAMPP
* Git & GitHub

---

# 📂 Project Structure

```
online-examination-system/
│
├── app.py
├── config.py
├── models.py
├── forms.py
├── routes/
├── templates/
├── static/
├── extensions.py
├── schema.sql
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/online-examination-system.git
```

### 2. Navigate to the Project

```bash
cd online-examination-system
```

### 3. Create a Virtual Environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Database

* Start MySQL using XAMPP.
* Create a new database.
* Import the `schema.sql` file.
* Update the database credentials in `config.py`.

### 6. Run the Application

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
```

# 👥 User Roles

#👨‍💼 Admin

* Manage teachers
* Manage students
* Manage subjects
* Create examinations
* View reports

# 👨‍🏫 Teacher

* Create exams
* Add questions
* Manage question bank
* View student performance

# 👨‍🎓 Student

* Login securely
* Attend online examinations
* Webcam verification during exams
* View examination results

# 📸 AI-Based Proctoring

The system integrates **OpenCV** for webcam-based monitoring during examinations.

Features include:

* Face detection
* Continuous webcam monitoring
* Enhanced examination security
* Reduced chances of impersonation

# 🔒 Security Features

* Flask-Login authentication
* Password protection
* CSRF protection
* Session management
* Role-based authorization
* Input validation

# 📊 Database

The application stores information related to:

* Users
* Students
* Teachers
* Subjects
* Exams
* Questions
* Results

using a **MySQL** relational database.

# 🎯 Future Enhancements

* Face Recognition Authentication
* AI-based Cheating Detection
* Live Video Monitoring
* Email Notifications
* OTP Login
* PDF Result Reports
* Analytics Dashboard
* Cloud Deployment

# 📄 License

This project is intended for educational and learning purposes.


# 👨‍💻 Author

Ravi Kumar Paswan

BCA Student | Python & Flask Developer | Web Developer
