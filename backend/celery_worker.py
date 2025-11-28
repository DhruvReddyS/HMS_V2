# celery_worker.py

from celery import Celery
from celery.schedules import crontab
from flask import Flask
from datetime import datetime, timedelta, date
from config import Config
from models import db, User, Patient, Doctor, Appointment, Treatment

import os
from flask_mail import Message
from mail_config import mail  # Flask-Mail instance


# ============================================================
#                CELERY + REDIS CONFIG
# ============================================================

celery = Celery(
    "hms",
    broker="redis://localhost:6379/0",      # Queue broker
    backend="redis://localhost:6379/1",     # Task results
)

# Minimal Flask app context for DB access inside tasks
flask_app = Flask(__name__)
flask_app.config.from_object(Config)
db.init_app(flask_app)
mail.init_app(flask_app)

# Directory to store exported CSVs
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")

# How long to keep CSV files (in days) – used by export_tasks
EXPORT_RETENTION_DAYS = 7


# ============================================================
#                   UTILITY FUNCTIONS
# ============================================================

def _pretty_status(status):
    if not status:
        return "Unknown"
    s = status.upper()
    if s == "COMPLETED":
        return "Completed"
    if s == "CANCELLED":
        return "Cancelled"
    if s == "BOOKED":
        return "Booked"
    return status


def _send_email(to, subject, html):
    """
    Helper for sending emails.
    Replace with Google Chat Webhook / SMS if needed.
    """
    if not to:
        return
    try:
        with flask_app.app_context():
            msg = Message(
                subject=subject,
                recipients=[to],
                html=html,
                sender="hms-noreply@example.com",
            )
            mail.send(msg)
    except Exception as e:
        print("Email sending failed:", e)


def _get_patient_email(patient):
    """
    Try to resolve patient email from either Patient.email or Patient.user.email.
    """
    if patient is None:
        return None
    # If Patient model has its own email field
    if getattr(patient, "email", None):
        return patient.email
    # If Patient is linked to User
    if getattr(patient, "user", None) and getattr(patient.user, "email", None):
        return patient.user.email
    return None


def _get_doctor_email(doctor):
    """
    Try to resolve doctor email from either Doctor.email or Doctor.user.email.
    """
    if doctor is None:
        return None
    if getattr(doctor, "email", None):
        return doctor.email
    if getattr(doctor, "user", None) and getattr(doctor.user, "email", None):
        return doctor.user.email
    return None


def _get_doctor_name(doctor):
    """
    Resolve a nice display name for the doctor.
    """
    if doctor is None:
        return "Doctor"
    if getattr(doctor, "full_name", None):
        return doctor.full_name
    if getattr(doctor, "name", None):
        return doctor.name
    if getattr(doctor, "user", None) and getattr(doctor.user, "fullname", None):
        return doctor.user.fullname
    return "Doctor"


def _get_patient_name(patient):
    """
    Resolve a nice display name for the patient.
    """
    if patient is None:
        return "Patient"
    if getattr(patient, "full_name", None):
        return patient.full_name
    if getattr(patient, "name", None):
        return patient.name
    if getattr(patient, "user", None) and getattr(patient.user, "fullname", None):
        return patient.user.fullname
    return "Patient"


# ============================================================
#     CELERY BEAT SCHEDULE (PERIODIC JOBS)
# ============================================================

# These task names are defined in tasks/scheduled_tasks.py
celery.conf.beat_schedule = {
    "daily-appointment-reminders": {
        "task": "send_daily_appointment_reminders",
        "schedule": crontab(hour=9, minute=0),   # every morning at 9 AM
    },
    "monthly-doctor-reports": {
        "task": "generate_and_send_monthly_reports",
        "schedule": crontab(day_of_month=1, hour=8, minute=0),  # 1st of month @ 8 AM
    },
}

celery.conf.timezone = "Asia/Kolkata"


# ============================================================
#     REGISTER TASK MODULES SO CELERY CAN DISCOVER THEM
# ============================================================

import tasks.export_tasks       # export_patient_history_csv
import tasks.scheduled_tasks    # send_daily_appointment_reminders, generate_and_send_monthly_reports
