# 🏥 HMS V2 – Hospital Management System

Role-based Hospital Management System built with:

- **Backend:** Flask (REST API, JWT auth, SQLite, Celery/Redis ready)
- **Frontend:** Vue 3 + Vite + Bootstrap
- **DB:** SQLite (dev) via SQLAlchemy
- **Auth:** JWT (Flask-JWT-Extended)

Supports **Admin**, **Doctor**, and **Patient** flows with separate dashboards.

---

## 🚀 Features

### 👨‍💼 Admin

- Login as admin and view **dashboard stats**
- **Manage doctors**
  - Create / view / update / delete doctors
  - Activate / deactivate doctors
- **Manage patients**
  - View / edit / delete patients
- **Manage appointments**
  - View all appointments
  - Update status (BOOKED / COMPLETED / CANCELLED)

---

### 👨‍⚕️ Doctor

- Personal **doctor dashboard** (summary)
- View **upcoming appointments**
- Mark appointments as **COMPLETED / CANCELLED**
- Add **treatment details** per appointment:
  - Visit type (online / in-person)
  - Tests done / advised
  - Diagnosis
  - Medicines & dosage pattern
  - Precautions, notes
  - Follow-up date
- View **patient history** (visit-wise + treatments)
- View own **availability** grid

---

### 👤 Patient

- **Patient dashboard** with profile info
- View & edit **profile** (contact + basic medical profile)
- **Departments** → list of specializations → doctors
- Browse **doctors** by department and search
- **Book appointments**
  - Doctor + date picker
  - Fetch available slots (green free / red booked)
  - Confirm with reason/symptoms
- View **My Appointments** (BOOKED / COMPLETED / CANCELLED)
- **Detailed Visit History** with diagnosis, tests, medicines, precautions etc. (per visit)

---

## 📁 Project Structure

```text
HMS_V2/
├── backend/
│   ├── app.py              # Flask app factory & routes wiring
│   ├── config.py           # Config class (DB URI, JWT secret, etc.)
│   ├── models.py           # User, Patient, Doctor, Appointment, Treatment
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── admin_routes.py
│   │   ├── doctor_routes.py
│   │   └── patient_routes.py
│   ├── seed.py             # Dev seeder (admin, doctors, patients, appointments, treatments)
│   ├── requirements.txt    # Generated via pip freeze
│   └── hms.db              # SQLite DB (created at runtime)
│
└── frontend/
    ├── index.html
    ├── package.json        # npm scripts & deps
    ├── vite.config.js
    └── src/
        ├── api/axios.js
        ├── router/index.js
        ├── store/authStore.js
        ├── App.vue
        └── views/
            ├── LandingPage.vue
            ├── LoginView.vue
            ├── RegisterView.vue
            ├── admin/...
            ├── doctor/...
            └── patient/...
