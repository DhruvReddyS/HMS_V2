# routes/patient_routes.py

from flask import request, jsonify, send_file, abort, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date
import os
import re
import csv
from io import StringIO

from celery.result import AsyncResult

from models import (
    db,
    User,
    Patient,
    Doctor,
    Appointment,
    Treatment,
    DoctorAvailability,   # NEW: availability table
)

from celery_worker import celery
from tasks.export_tasks import export_patient_history_csv

from cache_utils import cached, cache_delete_pattern  # ✅ Redis caching helpers

# Same slot grid as doctor weekly availability (1–2 PM break)
DEFAULT_TIME_SLOTS = [
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    # 13:00–14:00 is lunch break → no slots here
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
]


# -----------------------------------
# Helpers
# -----------------------------------
def _get_current_patient():
    """
    Resolves the current JWT user and ensures they are a patient.
    Uses 1–1 mapping: Patient.id == User.id
    """
    raw_id = get_jwt_identity()
    if raw_id is None:
        return None, None

    try:
        user_id = int(raw_id)
    except (TypeError, ValueError):
        return None, None

    user = User.query.get(user_id)
    if not user or user.role != "patient":
        return None, None

    patient = Patient.query.get(user_id)
    return user, patient


def _require_patient():
    """
    Helper for endpoints that are strictly patient-only, returning:
      (ok: bool, identity: dict | None, response: flask.Response | None)
    """
    claims = get_jwt()
    role = claims.get("role")

    if role != "patient":
        return False, None, (jsonify({"message": "Patient access required"}), 403)

    user_id = get_jwt_identity()
    if user_id is None:
        return False, None, (jsonify({"message": "Invalid token"}), 401)

    return True, {"id": int(user_id)}, None


# -----------------------------------
# GET /api/patient/profile
#   → Patient dashboard & profile page
# -----------------------------------
@jwt_required()
def get_patient_profile():
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    return jsonify({
        "id": patient.id,
        "full_name": patient.full_name,
        "username": user.username,
        "email": user.email,
        "gender": patient.gender,
        "dob": patient.dob,
        "address": patient.address,
        "phone": patient.phone,
        "height_cm": patient.height_cm,
        "weight_kg": patient.weight_kg,
        "blood_group": patient.blood_group,
        "is_disabled": patient.is_disabled,
        # kept so UI can show image if you ever set it from admin/db
        "profile_photo_url": patient.profile_photo_url,
    }), 200


# -----------------------------------
# PUT /api/patient/profile
#   → Patient can update own health/contact info.
# -----------------------------------
@jwt_required()
def update_patient_profile():
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    data = request.get_json() or {}

    patient.full_name = data.get("full_name", patient.full_name)
    patient.address = data.get("address", patient.address)
    patient.phone = data.get("phone", patient.phone)
    patient.gender = data.get("gender", patient.gender)
    patient.dob = data.get("dob", patient.dob)  # "YYYY-MM-DD" string

    # Numeric fields – safe parsing
    if "height_cm" in data:
        try:
            patient.height_cm = (
                float(data["height_cm"]) if data["height_cm"] is not None else None
            )
        except (TypeError, ValueError):
            pass

    if "weight_kg" in data:
        try:
            patient.weight_kg = (
                float(data["weight_kg"]) if data["weight_kg"] is not None else None
            )
        except (TypeError, ValueError):
            pass

    patient.blood_group = data.get("blood_group", patient.blood_group)

    if "is_disabled" in data:
        val = data["is_disabled"]
        if isinstance(val, bool) or val is None:
            patient.is_disabled = val

    # Notice: profile_photo_url is NOT changed here (no upload route).
    db.session.commit()
    return jsonify({"message": "Profile updated successfully"}), 200


# -----------------------------------
# GET /api/patient/doctors
#   → List of doctors for dropdown / browsing.
#   (Cached, same for all patients)
# -----------------------------------
@jwt_required()
@cached(prefix="patient_doctors", ttl=300)
def list_patient_doctors():
    doctors = (
        Doctor.query
        .join(User, Doctor.id == User.id)
        .filter(User.role == "doctor", User.is_active.is_(True))
        .all()
    )

    result = []
    for d in doctors:
        result.append({
            "id": d.id,
            "full_name": d.full_name,
            "specialization": d.specialization,
            "experience_years": d.experience_years,
            "about": d.about,
        })

    # return dict/list so @cached can jsonify + store
    return result


# -----------------------------------
# GET /api/patient/available-slots?doctor_id=&date=YYYY-MM-DD
#
#   → Returns slots with status: "free" / "booked"
#   (Cached per doctor_id+date)
# -----------------------------------
@jwt_required()
@cached(prefix="patient_slots", ttl=30)
def patient_available_slots():
    doctor_id = request.args.get("doctor_id", type=int)
    date_str = request.args.get("date")

    if not doctor_id or not date_str:
        return {"message": "doctor_id and date are required"}, 400

    # Ensure doctor exists AND is active from admin side
    doctor = (
        Doctor.query
        .join(User, Doctor.id == User.id)
        .filter(
            Doctor.id == doctor_id,
            User.role == "doctor",
            User.is_active.is_(True),
        )
        .first()
    )
    if not doctor:
        return {"message": "Doctor not found or inactive"}, 404

    # Validate date
    try:
        appt_date = datetime.fromisoformat(date_str).date()
    except Exception:
        return {"message": "Invalid date format"}, 400

    # Optional: disallow past dates
    if appt_date < date.today():
        return {"message": "Date cannot be in the past"}, 400

    # ---- 1) Doctor-specific availability overrides ----
    overrides = (
        DoctorAvailability.query
        .filter_by(doctor_id=doctor.id, date=date_str)
        .all()
    )
    override_map = {o.time_slot: o.is_available for o in overrides}

    # ---- 2) Appointments that block slots (anything not CANCELLED) ----
    booked = (
        Appointment.query
        .filter_by(doctor_id=doctor.id, date=date_str)
        .filter(Appointment.status != "CANCELLED")
        .all()
    )
    booked_slots = {a.time for a in booked}

    # ---- 3) Build final slots (same grid as doctor weekly view) ----
    detailed_slots = []
    for ts in DEFAULT_TIME_SLOTS:
        # First check if there is an appointment on that slot
        if ts in booked_slots:
            status = "booked"
        else:
            # then check doctor's availability override
            is_av = override_map.get(ts, True)  # default True = available
            status = "free" if is_av else "booked"

        detailed_slots.append({
            "time": ts,
            "status": status,
        })

    return {"slots": detailed_slots}


# -----------------------------------
# GET /api/patient/appointments
#   → List all appointments for logged-in patient.
#   (NOT cached → per-patient + frequently changing)
# -----------------------------------
@jwt_required()
def get_patient_appointments():
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    appts = (
        Appointment.query
        .filter_by(patient_id=patient.id)
        .order_by(Appointment.date.desc(), Appointment.created_at.desc())
        .all()
    )

    result = [a.to_patient_dict() for a in appts]
    return jsonify(result), 200


# -----------------------------------
# GET /api/patient/appointments/<appointment_id>
#   → Detailed view for a single appointment.
# -----------------------------------
@jwt_required()
def get_single_patient_appointment(appointment_id):
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    appt = (
        Appointment.query
        .filter_by(id=appointment_id, patient_id=patient.id)
        .first()
    )
    if not appt:
        return jsonify({"message": "Appointment not found"}), 404

    return jsonify(appt.to_patient_dict()), 200


# -----------------------------------
# POST /api/patient/appointments
#   → Create a new appointment.
# -----------------------------------
@jwt_required()
def create_patient_appointment():
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    data = request.get_json() or {}

    doctor_id = data.get("doctor_id")
    date_str = data.get("appointment_date")  # "YYYY-MM-DD"
    time_slot = data.get("time_slot")        # "HH:MM"
    reason = (data.get("reason") or "").strip() or None

    if not doctor_id or not date_str or not time_slot:
        return jsonify({
            "message": "doctor_id, appointment_date and time_slot are required"
        }), 400

    # Doctor must exist AND be active
    doctor = (
        Doctor.query
        .join(User, Doctor.id == User.id)
        .filter(
            Doctor.id == doctor_id,
            User.role == "doctor",
            User.is_active.is_(True),
        )
        .first()
    )
    if not doctor:
        return jsonify({"message": "Doctor not found or inactive"}), 404

    # Validate date
    try:
        appt_date = datetime.fromisoformat(date_str).date()
    except Exception:
        return jsonify({"message": "Invalid appointment_date format"}), 400

    if appt_date < date.today():
        return jsonify({"message": "Appointment date cannot be in the past"}), 400

    # Check slot not already booked (excluding cancelled)
    existing = (
        Appointment.query
        .filter_by(doctor_id=doctor.id, date=date_str, time=time_slot)
        .filter(Appointment.status != "CANCELLED")
        .first()
    )

    if existing:
        return jsonify({"message": "This time slot is already booked"}), 409

    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        date=date_str,
        time=time_slot,
        reason=reason,
        status="BOOKED",
    )

    db.session.add(appt)
    db.session.commit()

    # 🔥 Invalidate caches impacted by new appointment
    cache_delete_pattern("API:patient_slots:*")
    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")

    return jsonify({
        "message": "Appointment booked successfully",
        "appointment": appt.to_patient_dict(),
    }), 201


# -----------------------------------
# POST /api/patient/appointments/<appointment_id>/cancel
#   → Cancel an upcoming appointment.
# -----------------------------------
@jwt_required()
def cancel_patient_appointment(appointment_id):
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    appt = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id,
    ).first()

    if not appt:
        return jsonify({"message": "Appointment not found"}), 404

    if appt.status == "CANCELLED":
        return jsonify({"message": "Already cancelled"}), 200

    # don't allow cancelling COMPLETED appointments
    try:
        appt_date = datetime.fromisoformat(str(appt.date)).date()
    except Exception:
        appt_date = None

    if appt.status == "COMPLETED":
        return jsonify({"message": "Cannot cancel a completed appointment"}), 400

    # Optional: restrict cancelling past appointments
    if appt_date and appt_date < date.today():
        return jsonify({"message": "Cannot cancel past appointments"}), 400

    appt.status = "CANCELLED"
    db.session.commit()

    # 🔥 Invalidate caches impacted by cancellation
    cache_delete_pattern("API:patient_slots:*")
    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")

    return jsonify({"message": "Appointment cancelled successfully"}), 200


# -----------------------------------
# GET /api/patient/history
#
#   → Visit history for patient including treatments.
#   (NOT cached – per-patient & sensitive)
# -----------------------------------
@jwt_required()
def get_patient_history():
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    appts = (
        Appointment.query
        .filter_by(patient_id=patient.id)
        .order_by(Appointment.date.desc(), Appointment.created_at.desc())
        .all()
    )

    history = []
    for a in appts:
        # base appointment data (doctor_name, specialization, reason, etc.)
        item = a.to_patient_dict()

        if a.treatments:
            # latest treatment for this visit
            latest_t = max(a.treatments, key=lambda x: x.created_at or datetime.min)
            item["treatment"] = latest_t.to_dict()

            # full treatment history for that appointment
            item["all_treatments"] = [t.to_dict() for t in a.treatments]
        else:
            item["treatment"] = None
            item["all_treatments"] = []

        history.append(item)

    return jsonify(history), 200


# -----------------------------------
# GET /api/patient/history/export-csv
#
#   → Simple sync CSV export for current patient (no Celery).
# -----------------------------------
@jwt_required()
def patient_history_export_csv():
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    appts = (
        Appointment.query
        .filter_by(patient_id=patient.id)
        .order_by(Appointment.date.desc(), Appointment.created_at.desc())
        .all()
    )

    if not appts:
        return jsonify({"message": "No history found to export"}), 404

    # Build CSV in memory
    output = StringIO()
    writer = csv.writer(output)

    headers = [
        "Date", "Time", "Doctor", "Specialization", "Reason", "Status",
        "Diagnosis", "Visit type", "Tests", "Follow-up date",
        "Medicines", "Precautions", "Advice / Notes",
    ]
    writer.writerow(headers)

    for a in appts:
        t = a.treatments[-1] if a.treatments else None

        doctor_name = f"Dr. {a.doctor.full_name}" if a.doctor else ""
        specialization = a.doctor.specialization if a.doctor else ""

        diagnosis = getattr(t, "diagnosis", "") if t else ""
        visit_type = getattr(t, "visit_type", "") if t else ""
        tests_text = getattr(t, "tests_text", "") if t else ""

        # SAFE follow_up_date (string OR date/datetime)
        follow_up_date = ""
        if t and getattr(t, "follow_up_date", None):
            fud = t.follow_up_date
            if isinstance(fud, (datetime, date)):
                follow_up_date = fud.strftime("%Y-%m-%d")
            else:
                follow_up_date = str(fud)

        prescription = getattr(t, "prescription", "") if t else ""
        precautions = getattr(t, "precautions", "") if t else ""
        notes = getattr(t, "notes", "") if t else ""

        row = [
            a.date,
            a.time,
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

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            # what the browser will show as filename
            "Content-Disposition": "attachment; filename=visit_history.csv"
        },
    )


# =====================================================
# EXPORT VISIT HISTORY (CSV) USING CELERY + REDIS
# =====================================================

# 1. Trigger export (async job)
# POST /api/patient/export-history
@jwt_required()
def patient_export_history():
    ok, identity, resp = _require_patient()
    if not ok:
        return resp

    patient_user_id = identity["id"]
    user = User.query.get(patient_user_id)
    if not user or user.role != "patient":
        return jsonify({"message": "Invalid patient"}), 400

    task = export_patient_history_csv.delay(patient_user_id)

    return jsonify({
        "message": "Export started. You will be notified when it's ready.",
        "task_id": task.id,
    }), 202


# 2. Check export status
# GET /api/patient/export-history/status/<task_id>
@jwt_required()
def patient_export_history_status(task_id):
    ok, identity, resp = _require_patient()
    if not ok:
        return resp

    result = AsyncResult(task_id, app=celery)
    state = result.state

    data = {
        "task_id": task_id,
        "state": state,   # PENDING / STARTED / SUCCESS / FAILURE / ...
        "ready": False,
    }

    if state == "SUCCESS":
        data["ready"] = True
    elif state == "FAILURE":
        data["error"] = str(result.info)

    return jsonify(data), 200


# 3. Download final CSV (Celery version)
# GET /api/patient/export-history/download/<task_id>
@jwt_required()
def patient_export_history_download(task_id):
    ok, identity, resp = _require_patient()
    if not ok:
        return resp

    patient_user_id = identity["id"]
    result = AsyncResult(task_id, app=celery)

    if result.state != "SUCCESS":
        return jsonify({"message": "Export not ready yet"}), 400

    file_path = result.result
    if not file_path or not isinstance(file_path, str):
        return jsonify({"message": "Invalid export result"}), 500

    # Security: ensure this file belongs to this patient
    # filename like: visit_history_patient_(id)_YYYY-MM-DDT...
    filename = os.path.basename(file_path)
    m = re.match(r"visit_history_patient_(\d+)_", filename)
    if not m or str(patient_user_id) != m.group(1):
        return jsonify({"message": "Not authorized to download this file"}), 403

    if not os.path.exists(file_path):
        abort(404, description="Export file not found on server")

    return send_file(
        file_path,
        mimetype="text/csv",
        as_attachment=True,
        download_name="visit-history.csv",
    )
