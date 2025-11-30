from datetime import date, timedelta, datetime
import io
from celery import shared_task
from flask import current_app, render_template
from xhtml2pdf import pisa
from celery_worker import flask_app, _send_email
from models import User, Patient, Doctor, Appointment, Treatment


def _html_to_pdf_bytes(html: str) -> bytes:
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        current_app.logger.error("Failed to generate PDF for monthly report.")
        return b""
    return result.getvalue()


@shared_task(name="send_daily_appointment_reminders")
def send_daily_appointment_reminders():
    with flask_app.app_context():
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        appointments = (
            Appointment.query
            .filter(
                Appointment.date == today_str,
                Appointment.status == "BOOKED",
            )
            .all()
        )
        if not appointments:
            return "no_appointments"

        sent_count = 0
        for appt in appointments:
            patient = appt.patient
            doctor = appt.doctor
            if not patient or not doctor:
                continue

            patient_user = patient.user
            doctor_name = getattr(doctor, "full_name", None) or getattr(doctor, "name", None) or "Doctor"
            patient_name = getattr(patient, "full_name", None) or getattr(patient_user, "fullname", None) or "Patient"
            time_str = getattr(appt, "time", None) or "your scheduled time"

            subject = f"Appointment reminder - Dr. {doctor_name}"
            body = (
                f"Hello {patient_name},\n\n"
                f"This is a reminder that you have an appointment today with "
                f"Dr. {doctor_name} at {time_str}.\n\n"
                f"Please arrive a few minutes early.\n\n"
                f"Regards,\nHospital Management System"
            )

            try:
                _send_email(
                    to=patient_user.email,
                    subject=subject,
                    body=body,
                )
                sent_count += 1
            except Exception as e:
                current_app.logger.error(
                    f"Failed to send reminder for appointment {appt.id}: {e}"
                )

        return f"sent_{sent_count}_reminders"


@shared_task(name="generate_and_send_monthly_reports")
def generate_and_send_monthly_reports():
    with flask_app.app_context():
        today = date.today()
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)

        start = first_day_prev_month
        end = last_day_prev_month

        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        doctors = Doctor.query.all()
        if not doctors:
            return "no_doctors"

        report_count = 0

        for doctor in doctors:
            doctor_user = doctor.user
            doctor_name = getattr(doctor, "full_name", None) or getattr(doctor_user, "fullname", None) or "Doctor"

            completed_appts = (
                Appointment.query
                .filter(
                    Appointment.doctor_id == doctor.id,
                    Appointment.status == "COMPLETED",
                    Appointment.date >= start_str,
                    Appointment.date <= end_str,
                )
                .order_by(Appointment.date, Appointment.time)
                .all()
            )

            if not completed_appts:
                continue

            rows = []
            for appt in completed_appts:
                patient = appt.patient
                if not patient:
                    continue

                patient_user = patient.user

                try:
                    appt_date_obj = datetime.strptime(appt.date, "%Y-%m-%d")
                except Exception:
                    appt_date_obj = datetime.today()

                treatment = (
                    Treatment.query.filter_by(appointment_id=appt.id).first()
                    if hasattr(Treatment, "appointment_id")
                    else (appt.treatments[0] if appt.treatments else None)
                )

                rows.append({
                    "date": appt_date_obj,
                    "time": getattr(appt, "time", None),
                    "patient_name": getattr(patient, "full_name", None)
                        or getattr(patient_user, "fullname", None)
                        or "Patient",
                    "diagnosis": getattr(treatment, "diagnosis", "") if treatment else "",
                    "prescription": getattr(treatment, "prescription", "") if treatment else "",
                    "notes": getattr(treatment, "notes", "") if treatment else "",
                })

            if not rows:
                continue

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

            pdf_bytes = _html_to_pdf_bytes(html_body)
            attachments = []
            if pdf_bytes:
                pdf_filename = (
                    f"monthly_activity_report_{doctor_user.username}_"
                    f"{start.strftime('%Y_%m')}.pdf"
                )
                attachments.append(
                    (pdf_filename, pdf_bytes, "application/pdf")
                )

            try:
                _send_email(
                    to=doctor_user.email,
                    subject=subject,
                    html=html_body,
                    attachments=attachments if attachments else None,
                )
                report_count += 1
            except Exception as e:
                current_app.logger.error(
                    f"Failed to send monthly report to doctor {doctor.id}: {e}"
                )

        return f"monthly_reports_sent_{report_count}"
