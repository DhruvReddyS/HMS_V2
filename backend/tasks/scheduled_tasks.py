# tasks/scheduled_tasks.py

from datetime import date, timedelta

from celery import shared_task
from flask import current_app, render_template
from flask_mail import Message

from celery_worker import flask_app
from mail_config import mail
from models import User, Patient, Doctor, Appointment, Treatment


@shared_task(name="send_daily_appointment_reminders")
def send_daily_appointment_reminders():
    """
    Finds all 'BOOKED' appointments for today and sends email reminders to patients.
    Runs once per day via Celery Beat.
    """
    with flask_app.app_context():
        today = date.today()

        # Filter today's booked appointments
        appointments = (
            Appointment.query
            .filter(
                Appointment.date == today,
                Appointment.status == "BOOKED",
            )
            .all()
        )

        if not appointments:
            current_app.logger.info("No appointments for today, skipping reminders.")
            return "no_appointments"

        sent_count = 0

        for appt in appointments:
            patient = appt.patient
            doctor = appt.doctor
            if not patient or not doctor:
                continue

            patient_user = patient.user

            doctor_name = (
                getattr(doctor, "full_name", None)
                or getattr(doctor, "name", None)
                or "Doctor"
            )
            patient_name = (
                getattr(patient, "full_name", None)
                or getattr(patient_user, "fullname", None)
                or "Patient"
            )

            time_str = getattr(appt, "time", None) or "your scheduled time"

            subject = f"Appointment reminder - Dr. {doctor_name}"
            body = (
                f"Hello {patient_name},\n\n"
                f"This is a reminder that you have an appointment today with "
                f"Dr. {doctor_name} at {time_str}.\n\n"
                f"Please arrive a few minutes early.\n\n"
                f"Regards,\nHospital Management System"
            )

            msg = Message(
                subject=subject,
                recipients=[patient_user.email],
                body=body,
            )

            try:
                mail.send(msg)
                sent_count += 1
            except Exception as e:
                current_app.logger.error(
                    f"Failed to send reminder for appointment {appt.id}: {e}"
                )

        return f"sent_{sent_count}_reminders"


@shared_task(name="generate_and_send_monthly_reports")
def generate_and_send_monthly_reports():
    """
    Generates monthly HTML activity reports for each doctor and emails them.
    Runs on the 1st of every month via Celery Beat.
    """
    with flask_app.app_context():
        today = date.today()

        # Last month range
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)

        start = first_day_prev_month
        end = last_day_prev_month

        doctors = Doctor.query.all()
        if not doctors:
            return "no_doctors"

        report_count = 0

        for doctor in doctors:
            doctor_user: User = doctor.user  # doctor.user → User with email

            doctor_name = (
                getattr(doctor, "full_name", None)
                or getattr(doctor_user, "fullname", None)
                or "Doctor"
            )

            # Completed appointments in the period
            completed_appts = (
                Appointment.query
                .filter(
                    Appointment.doctor_id == doctor.id,
                    Appointment.status == "COMPLETED",
                    Appointment.date >= start,
                    Appointment.date <= end,
                )
                .order_by(Appointment.date, Appointment.time)
                .all()
            )

            if not completed_appts:
                # Optionally skip emailing if no appointments
                continue

            # Build a simple data structure for the template
            rows = []
            for appt in completed_appts:
                patient = appt.patient
                if not patient:
                    continue

                patient_user = patient.user

                # Use either relationship or direct query
                treatment = (
                    Treatment.query.filter_by(appointment_id=appt.id).first()
                    if hasattr(Treatment, "appointment_id")
                    else (appt.treatments[0] if appt.treatments else None)
                )

                rows.append({
                    "date": appt.date,
                    "time": getattr(appt, "time", None),
                    "patient_name": (
                        getattr(patient, "full_name", None)
                        or getattr(patient_user, "fullname", None)
                        or "Patient"
                    ),
                    "diagnosis": getattr(treatment, "diagnosis", "") if treatment else "",
                    "prescription": getattr(treatment, "prescription", "") if treatment else "",
                    "notes": getattr(treatment, "notes", "") if treatment else "",
                })

            if not rows:
                continue

            # Render HTML using template
            # templates/email/monthly_doctor_report.html
            html_body = render_template(
                "email/monthly_doctor_report.html",
                doctor_name=doctor_name,
                start_date=start,
                end_date=end,
                rows=rows,
            )

            subject = (
                f"Monthly Activity Report "
                f"({start.strftime('%b %Y')}) - Dr. {doctor_name}"
            )

            msg = Message(
                subject=subject,
                recipients=[doctor_user.email],
            )
            msg.html = html_body

            try:
                mail.send(msg)
                report_count += 1
            except Exception as e:
                current_app.logger.error(
                    f"Failed to send monthly report to doctor {doctor.id}: {e}"
                )

        return f"monthly_reports_sent_{report_count}"
