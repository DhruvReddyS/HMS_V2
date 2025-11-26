HMS V2 - Hospital Management System

A full-stack hospital management system with Admin, Doctor, and Patient modules.
Built using Flask (backend) and Vue 3 (frontend).

OVERVIEW

HMS V2 is a modern, role-based healthcare management system that supports:

• Admin portal
• Doctor portal
• Patient portal

Includes:

JWT authentication

Patient booking

Live doctor availability

Visit history with treatments

Advanced appointment workflows

Database seeding with 15 doctors, 50 patients, 300+ appointments

TECH STACK

Frontend:

Vue 3

Vite

Bootstrap 5

Axios

Vue Router

Backend:

Flask

SQLAlchemy

Flask-JWT-Extended

Flask-CORS

SQLite

Flask-Caching

FEATURES

ADMIN FEATURES:

Dashboard with hospital statistics

Manage doctors (add/edit/delete/activate/deactivate)

Manage patients

Manage all appointments

Update appointment status (BOOKED / COMPLETED / CANCELLED)

DOCTOR FEATURES:

Personalized doctor dashboard

View today/upcoming appointments

Update appointment status

Create detailed treatment records:
• Diagnosis
• Tests done / tests advised
• Medicines + dosage patterns
• Visit type (Online / In-person)
• Precautions
• Doctor Notes
• Follow-up date

View full patient history

PATIENT FEATURES:

Dashboard with profile summary

Edit personal + medical info

View departments and doctors

Real-time availability:
• Green = available
• Red = booked

Book appointments

View / cancel appointments

Visit history with full treatment breakdown:
• Diagnosis
• Tests
• Medicines
• Precautions
• Notes
• Follow-up dates

PROJECT STRUCTURE

HMS_V2/
│ backend/
│ app.py
│ models.py
│ config.py
│ seed.py
│ requirements.txt
│ routes/
│ auth_routes.py
│ admin_routes.py
│ doctor_routes.py
│ patient_routes.py
│
└ frontend/
index.html
package.json
src/
App.vue
router/index.js
store/authStore.js
views/

INSTALLATION INSTRUCTIONS

------------- BACKEND SETUP -------------

STEP 1 — Navigate to backend:
cd backend

STEP 2 — Create virtual environment:

Windows:
python -m venv venv
venv\Scripts\activate

Linux/Mac:
python3 -m venv venv
source venv/bin/activate

STEP 3 — Install dependencies:
pip install -r requirements.txt

STEP 4 — Run initial DB setup:
python app.py
(creates tables + default admin)

Press CTRL+C to stop backend.

STEP 5 — Seed database:
python seed.py
This seeds:

1 admin

15 doctors

50 patients

300+ appointments with treatments

Default login credentials:

ADMIN:
username: admin
password: admin123

DOCTORS:
doctor1 / doctor123
doctor2 / doctor123
…

PATIENTS:
patient1 / patient123
patient2 / patient123
…

STEP 6 — Run backend:
python app.py

Backend runs at:
http://127.0.0.1:5000/

------------- FRONTEND SETUP -------------

Open a NEW terminal.

STEP 1 — Navigate to frontend:
cd frontend

STEP 2 — Install node dependencies:
npm install

STEP 3 — Start dev server:
npm run dev

Frontend runs at:
http://localhost:5173/

LOGIN FLOW (JWT)

User logs in using username/password

Backend returns access_token + role

Frontend stores token in sessionStorage

Vue Router guards redirect users:

Admin → /admin/dashboard
Doctor → /doctor/dashboard
Patient → /patient/dashboard

Logout clears sessionStorage

DATABASE ERD

Users
↓ 1-1
Patient
↓ 1-N
Appointment
↓ 1-N
Treatment

Doctor also relates to Appointments.

ROUTE PROTECTION (Frontend)

• Admin routes start with /admin/...
• Doctor routes start with /doctor/...
• Patient routes start with /patient/...

Vue Router guards block unauthorized access.

API SUMMARY

AUTH:
POST /api/auth/login
POST /api/auth/register
GET /api/auth/me

ADMIN:
GET /api/admin/stats
GET /api/admin/doctors
POST /api/admin/doctors
PUT /api/admin/doctors/{id}
DELETE /api/admin/doctors/{id}
GET /api/admin/appointments
PUT /api/admin/appointments/{id}/status

DOCTOR:
GET /api/doctor/dashboard-summary
GET /api/doctor/appointments
POST /api/doctor/appointments/{id}/status
POST /api/doctor/appointments/{id}/treatment
GET /api/doctor/patient-history/{id}
GET /api/doctor/availability

PATIENT:
GET /api/patient/profile
PUT /api/patient/profile
GET /api/patient/doctors
GET /api/patient/available-slots
POST /api/patient/appointments
GET /api/patient/appointments
POST /api/patient/appointments/{id}/cancel
GET /api/patient/history

HOW TO PUSH TO GITHUB

git init
git remote add origin https://github.com/DhruvReddyS/HMS_V2.git

git add .
git commit -m "Initial HMS V2 full project"
git push --force origin main

CREDITS

Developed by: Dhruv Reddy
Tech: Flask + Vue 3