# EduReach — Remote Classroom Platform

A full-stack web application for remote classroom management, built with Python Flask and SQLite.

## Problem Statement

Educational institutions need a centralized platform for teachers to manage courses, materials, assignments, and attendance, while students need access to learning resources, quiz assessments, and progress tracking — all in a unified, accessible web interface.

## Features

### For Teachers
- Create and manage courses
- Upload learning materials
- Post announcements
- Create assignments with deadlines
- Mark student attendance
- View flagged students (low performance alerts)

### For Students
- Enroll in courses
- Access course materials and announcements
- Submit assignments
- Take quizzes with instant scoring
- View attendance percentage
- Earn achievement badges
- Receive personalized learning recommendations

### General
- Secure authentication with role-based access
- Multi-language support (English, Telugu, Hindi)
- Responsive, academic-themed UI
- File upload/download capabilities

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite (sqlite3)
- **Authentication**: flask-login + werkzeug.security
- **Frontend**: HTML, CSS, vanilla JavaScript

## How to Run Locally

1. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Default Users

On first run, sample data is created. You can register new teachers and students through the signup page.

## Deployment

The application is configured for deployment on platforms supporting Procfile (e.g., Heroku, Render).
