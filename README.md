# Hospital Management System (HMS)

A Full-Stack Web Application Using Flask, Vue.js, Redis, and Celery

---

## 1. Project Overview

The Hospital Management System (HMS) is a full-stack web application designed to streamline patient management, doctor scheduling, appointment handling, treatment tracking, and administrative analytics within a healthcare environment.

The system is developed using:

* Flask as the backend REST API
* Vue.js as the frontend interface
* Redis for caching and message brokering
* Celery for background task execution and scheduled jobs
* SQLite / MySQL as the database

### Supported User Roles

#### Admin

* Manage doctors and patients
* Monitor appointments
* Generate analytics and reports
* View monthly performance summaries

#### Doctor

* Manage appointments and patient visits
* Record treatments
* Maintain availability schedule
* Access patient medical history
* Generate monthly reports

#### Patient

* Book appointments
* View available time slots
* Access medical history
* Download CSV reports
* Update profile information

---

## 2. Technology Stack

### Backend

* Python 3.x
* Flask
* Flask-JWT-Extended
* Flask-SQLAlchemy
* Flask-Caching
* Flask-CORS
* Celery
* Redis
* ReportLab
* Pillow

### Frontend

* Vue.js (Vite)
* Axios
* Bootstrap / Bootstrap Icons

---

## 3. Key Features

### Admin Features

* Doctor and patient management
* Appointment monitoring
* Analytics and reporting
* Monthly PDF report generation

### Doctor Features

* Appointment dashboard (daily/weekly)
* Status updates
* Treatment logging
* Availability scheduling
* Patient history viewing
* Monthly PDF report generation

### Patient Features

* Appointment booking
* Time slot availability
* Medical history viewing
* CSV export
* Profile updates

### System Features

* Redis caching
* Celery workers for async tasks
* Celery beat scheduler for periodic tasks
* Background CSV generation

---

## 4. API Endpoints Summary (Single Table)

| Method   | Endpoint                                       | Description                    |
| -------- | ---------------------------------------------- | ------------------------------ |
| POST     | /api/auth/register                             | Register a new user            |
| POST     | /api/auth/login                                | Login and receive JWT token    |
| GET      | /api/auth/me                                   | Get authenticated user details |
| GET      | /api/admin/stats                               | Dashboard statistics           |
| GET      | /api/admin/reports-analytics                   | Analytics and charts           |
| GET      | /api/admin/monthly-report                      | Monthly PDF report             |
| POST     | /api/admin/doctors                             | Add a doctor                   |
| GET      | /api/admin/doctors                             | List doctors                   |
| GET      | /api/admin/doctors/<id>                        | Get doctor details             |
| PUT      | /api/admin/doctors/<id>                        | Update doctor                  |
| DELETE   | /api/admin/doctors/<id>                        | Delete doctor                  |
| GET      | /api/admin/patients                            | List patients                  |
| POST     | /api/admin/patients                            | Add patient                    |
| GET      | /api/admin/patients/<id>                       | Get patient details            |
| PUT      | /api/admin/patients/<id>                       | Update patient                 |
| DELETE   | /api/admin/patients/<id>                       | Delete patient                 |
| GET      | /api/admin/appointments                        | List appointments              |
| PUT      | /api/admin/appointments/<id>/status            | Update appointment status      |
| GET      | /api/doctor/dashboard-summary                  | Doctor dashboard summary       |
| GET/PUT  | /api/doctor/profile                            | Get/Update doctor profile      |
| GET      | /api/doctor/stats                              | Doctor statistics              |
| GET      | /api/doctor/monthly-report                     | Doctor monthly report          |
| GET      | /api/doctor/appointments                       | List doctor appointments       |
| POST     | /api/doctor/appointments/<id>/status           | Update status                  |
| POST/GET | /api/doctor/appointments/<id>/treatment        | Add/Get treatment details      |
| GET      | /api/doctor/availability                       | Weekly availability            |
| POST     | /api/doctor/availability/toggle                | Toggle slot availability       |
| POST     | /api/doctor/availability/bulk                  | Bulk update availability       |
| GET      | /api/doctor/my-patients                        | Doctor's patient list          |
| GET      | /api/doctor/patient-history                    | Patient history                |
| GET/PUT  | /api/patient/profile                           | Get/Update patient profile     |
| GET      | /api/patient/doctors                           | List doctors                   |
| GET      | /api/patient/available-slots                   | Available slots                |
| GET/POST | /api/patient/appointments                      | Manage appointments            |
| GET      | /api/patient/appointments/<id>                 | Appointment details            |
| POST     | /api/patient/appointments/<id>/cancel          | Cancel appointment             |
| GET      | /api/patient/history                           | Medical history                |
| GET      | /api/patient/history/export-csv                | Download CSV instantly         |
| POST     | /api/patient/export-history                    | Trigger CSV export             |
| GET      | /api/patient/export-history/status/<task_id>   | Export status                  |
| GET      | /api/patient/export-history/download/<task_id> | Download exported CSV          |

---

## 5. Installation & Setup Instructions

### Backend Setup

```
cd backend
pip install -r requirements.txt
```

### Frontend Setup

```
cd frontend
npm install
```

---

## 6. How to Run the Application

### Terminal 1 — Start Frontend

```
cd frontend
npm run dev
```

Accessible at: [http://localhost:5173](http://localhost:5173)

### PowerShell — Start Redis (Docker)

```
docker run -d --name redis-hms -p 6379:6379 redis:7-alpine
docker ps -a
docker start redis-hms
docker ps
```

### Terminal 2 — Celery Worker

```
cd backend
celery -A celery_worker.celery worker --loglevel=info --pool=solo
```

### Terminal 3 — Celery Beat Scheduler

```
cd backend
celery -A celery_worker.celery beat --loglevel=info
```

### Terminal 4 — Flask Backend

```
cd backend
python app.py
```

Backend runs at: [http://localhost:5000](http://localhost:5000)

---

## 7. Running Scheduled Tasks Manually

### Generate Monthly Reports

```
celery -A celery_worker.celery call generate_and_send_monthly_reports
```

### Send Daily Appointment Reminders

```
celery -A celery_worker.celery call send_daily_appointment_reminders
```

---

## 8. Backend Requirements (requirements.txt)

```
Flask
Flask-CORS
Flask-JWT-Extended
Flask-SQLAlchemy
Flask-Caching
Flask-Mail
python-dotenv
Werkzeug
itsdangerous

celery
redis

reportlab
pillow

SQLAlchemy
click
blinker
```

---

## 9. Frontend Dependencies

Listed in package.json:

* Vue 3
* Axios
* Bootstrap / Bootstrap Icons
* Vite

---

## 10. Project Structure

```
backend/
    app.py
    models.py
    celery_worker.py
    routes/
    tasks/
    exports/
    cache_utils.py

frontend/
    src/
    public/
```

---

## 11. Academic Integrity Note

* Do not upload code publicly
* Do not share project files
* Ensure you understand and can explain all logic
* All code must be your own to main
