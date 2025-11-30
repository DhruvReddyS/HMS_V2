from celery import Celery
from celery.schedules import crontab
from flask import Flask
from datetime import datetime, timedelta, date
from config import Config
from models import db, User, Patient, Doctor, Appointment, Treatment

import os
from flask_mail import Message
from mail_config import mail


celery = Celery(
    "hms",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

flask_app = Flask(__name__)
flask_app.config.from_object(Config)
db.init_app(flask_app)
mail.init_app(flask_app)

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
EXPORT_RETENTION_DAYS = 7


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


def _send_email(to, subject, body=None, html=None, attachments=None):
    if not to:
        return

    try:
        with flask_app.app_context():
            msg = Message(
                subject=subject,
                recipients=[to],
            )

            if body is not None:
                msg.body = body
            if html is not None:
                msg.html = html

            if attachments:
                for filename, data, mimetype in attachments:
                    msg.attach(
                        filename=filename,
                        content_type=mimetype,
                        data=data,
                    )

            mail.send(msg)
    except Exception as e:
        print("Email sending failed:", e)


def _get_patient_email(patient):
    if patient is None:
        return None
    if getattr(patient, "email", None):
        return patient.email
    if getattr(patient, "user", None) and getattr(patient.user, "email", None):
        return patient.user.email
    return None


def _get_doctor_email(doctor):
    if doctor is None:
        return None
    if getattr(doctor, "email", None):
        return doctor.email
    if getattr(doctor, "user", None) and getattr(doctor.user, "email", None):
        return doctor.user.email
    return None


def _get_doctor_name(doctor):
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
    if patient is None:
        return "Patient"
    if getattr(patient, "full_name", None):
        return patient.full_name
    if getattr(patient, "name", None):
        return patient.name
    if getattr(patient, "user", None) and getattr(patient.user, "fullname", None):
        return patient.user.fullname
    return "Patient"


celery.conf.beat_schedule = {
    "daily-appointment-reminders": {
        "task": "send_daily_appointment_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    "monthly-doctor-reports": {
        "task": "generate_and_send_monthly_reports",
        "schedule": crontab(day_of_month=1, hour=8, minute=0),
    },
}

celery.conf.timezone = "Asia/Kolkata"


import tasks.export_tasks
import tasks.scheduled_tasks
