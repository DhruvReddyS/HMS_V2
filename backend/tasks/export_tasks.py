# tasks/export_tasks.py

import os
import csv
from datetime import datetime, timedelta, date

from celery_worker import celery, EXPORT_DIR, flask_app, EXPORT_RETENTION_DAYS
from models import User, Patient, Appointment


def _cleanup_old_exports(retention_days: int = EXPORT_RETENTION_DAYS) -> int:
    """
    Delete CSV files in EXPORT_DIR older than `retention_days` days.

    This runs inside the Celery worker process whenever a new export is created.
    It WILL ONLY delete files whose modified time is strictly older than
    (now - retention_days). Returns how many files were deleted.
    """
    if not os.path.exists(EXPORT_DIR):
        return 0

    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    deleted = 0

    for fname in os.listdir(EXPORT_DIR):
        # Only touch CSV files
        if not fname.lower().endswith(".csv"):
            continue

        fpath = os.path.join(EXPORT_DIR, fname)
        try:
            stat = os.stat(fpath)
        except FileNotFoundError:
            continue

        mtime = datetime.utcfromtimestamp(stat.st_mtime)
        if mtime < cutoff:
            try:
                os.remove(fpath)
                deleted += 1
            except OSError:
                # Ignore delete errors; we don't want the task to fail because of this
                pass

    return deleted


def _cleanup_old_exports_for_patient(patient_id: int) -> int:
    """
    Keep only the newest CSV export file for this patient.
    Deletes all older CSVs whose name starts with:
      visit_history_patient_<patient_id>_
    Returns the number of deleted files.
    """
    if not os.path.exists(EXPORT_DIR):
        return 0

    prefix = f"visit_history_patient_{patient_id}_"
    files = [
        f for f in os.listdir(EXPORT_DIR)
        if f.startswith(prefix) and f.endswith(".csv")
    ]

    # Nothing or only one file → nothing to clean
    if len(files) <= 1:
        return 0

    # Filenames contain timestamp, so lexical sort = chronological order
    files.sort()
    to_delete = files[:-1]   # keep only the last (newest)
    deleted = 0

    for fname in to_delete:
        try:
            os.remove(os.path.join(EXPORT_DIR, fname))
            deleted += 1
        except OSError:
            # Ignore delete errors
            pass

    return deleted


@celery.task(name="export_patient_history_csv")
def export_patient_history_csv(patient_user_id: int) -> str:
    """
    Build a CSV of a single patient's visit history and save it under EXPORT_DIR.
    Returns the absolute file path as the Celery task result.

    Mapping assumption:
      - 1–1 mapping: Patient.id == User.id
      - Appointment.patient_id == Patient.id (== User.id)

    Used by:
      - POST /api/patient/export-history
      - GET  /api/patient/export-history/download/<task_id>
    """
    with flask_app.app_context():
        user = User.query.get(patient_user_id)
        if not user or user.role != "patient":
            raise ValueError("Invalid patient user id")

        # 1–1 mapping: Patient.id == User.id
        patient = Patient.query.get(patient_user_id)
        if not patient:
            raise ValueError("No patient record found for this user")

        # Appointments linked via patient_id == patient.id
        appts = (
            Appointment.query
            .filter_by(patient_id=patient.id)
            .order_by(Appointment.date.desc(), Appointment.created_at.desc())
            .all()
        )

        # Make sure directory exists
        os.makedirs(EXPORT_DIR, exist_ok=True)

        # Build filename like:
        # visit_history_patient_35_2025-11-28T23-59-12.csv
        ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"visit_history_patient_{patient.id}_{ts}.csv"
        file_path = os.path.join(EXPORT_DIR, filename)

        headers = [
            "Date", "Time", "Doctor", "Specialization", "Reason", "Status",
            "Diagnosis", "Visit type", "Tests", "Follow-up date",
            "Medicines", "Precautions", "Advice / Notes",
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for a in appts:
                # Latest treatment for that appointment (if any)
                t = None
                if a.treatments:
                    # Use created_at if present; fallback to oldest
                    t = max(
                        a.treatments,
                        key=lambda x: x.created_at or datetime.min,
                    )

                doctor = a.doctor  # relationship

                doctor_name = f"Dr. {doctor.full_name}" if doctor else ""
                specialization = doctor.specialization if doctor else ""

                # Safely read treatment fields (they can be None OR strings/dates)
                diagnosis = getattr(t, "diagnosis", "") if t else ""
                visit_type = getattr(t, "visit_type", "") if t else ""
                tests_text = getattr(t, "tests_text", "") if t else ""

                follow_up_raw = getattr(t, "follow_up_date", None) if t else None
                if isinstance(follow_up_raw, (datetime, date)):
                    follow_up_date = follow_up_raw.strftime("%Y-%m-%d")
                else:
                    follow_up_date = follow_up_raw or ""

                prescription = getattr(t, "prescription", "") if t else ""
                precautions = getattr(t, "precautions", "") if t else ""
                notes = getattr(t, "notes", "") if t else ""

                row = [
                    a.date,                     # can be date or string
                    a.time,                     # "HH:MM"
                    doctor_name,
                    specialization,
                    a.reason or "",
                    (a.status or "").capitalize(),
                    diagnosis,
                    visit_type,
                    tests_text,
                    follow_up_date,
                    prescription,
                    precautions,
                    notes,
                ]
                writer.writerow(row)

    # Per-patient cleanup: keep only latest CSV for this patient
    _cleanup_old_exports_for_patient(patient_user_id)

    # Global time-based cleanup (older than EXPORT_RETENTION_DAYS)
    _cleanup_old_exports()

    return file_path
