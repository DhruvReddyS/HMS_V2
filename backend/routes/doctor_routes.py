# routes/doctor_routes.py

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, time as dtime, timedelta

from models import db, User, Patient, Doctor, Appointment, Treatment


# -----------------------------
# Helper: get current doctor
# -----------------------------
def _get_current_doctor():
    """
    Resolves the current JWT user and ensures they are a doctor.
    Uses 1–1 mapping: Doctor.id == User.id
    """
    user_id = get_jwt_identity()
    if not user_id:
        return None, None

    user = User.query.get(user_id)
    if not user or user.role != "doctor":
        return None, None

    doctor = Doctor.query.get(user_id)
    return user, doctor


# -----------------------------
# GET /api/doctor/dashboard-summary
#
# → Top section: upcoming appts + counts
# -----------------------------
@jwt_required()
def doctor_dashboard_summary():
    user, doctor = _get_current_doctor()
    if not doctor:
        return jsonify({"message": "Doctor not found or invalid role"}), 404

    today = date.today().strftime("%Y-%m-%d")

    upcoming_q = (
        Appointment.query
        .filter_by(doctor_id=doctor.id)
        .filter(Appointment.date >= today)
        .filter(Appointment.status != "CANCELLED")
        .order_by(Appointment.date.asc(), Appointment.time.asc())
    )

    upcoming = upcoming_q.limit(5).all()

    # distinct active patients (ever)
    patient_ids = {
        a.patient_id for a in
        Appointment.query.filter_by(doctor_id=doctor.id).all()
    }
    patients_count = len(patient_ids)

    upcoming_payload = []
    for a in upcoming:
        p = a.patient
        upcoming_payload.append({
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": p.full_name if p and p.full_name else f"Patient #{a.patient_id}",
            "appointment_date": a.date,
            "time_slot": a.time,
            "status": a.status,
            "reason": a.reason,
        })

    return jsonify({
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "specialization": doctor.specialization,
            "experience_years": doctor.experience_years,
        },
        "stats": {
            "upcoming_count": upcoming_q.count(),
            "patients_count": patients_count,
        },
        "upcoming": upcoming_payload,
    }), 200


# -----------------------------
# GET /api/doctor/appointments
#   ?scope=today|upcoming|all
# -----------------------------
@jwt_required()
def doctor_appointments():
    user, doctor = _get_current_doctor()
    if not doctor:
        return jsonify({"message": "Doctor not found or invalid role"}), 404

    scope = (request.args.get("scope") or "upcoming").lower()
    today_str = date.today().strftime("%Y-%m-%d")

    q = Appointment.query.filter_by(doctor_id=doctor.id)

    if scope == "today":
        q = q.filter(Appointment.date == today_str)
    elif scope == "upcoming":
        q = (
            q.filter(Appointment.date >= today_str)
             .filter(Appointment.status != "CANCELLED")
        )
    # scope == "all" → no extra filter

    q = q.order_by(Appointment.date.asc(), Appointment.time.asc())

    items = []
    for a in q.all():
        p = a.patient
        items.append({
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": p.full_name if p and p.full_name else f"Patient #{a.patient_id}",
            "appointment_date": a.date,
            "time_slot": a.time,
            "status": a.status,
            "reason": a.reason,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return jsonify(items), 200


# -----------------------------
# POST /api/doctor/appointments/<appt_id>/status
#   { "status": "CANCELLED" | "BOOKED" | "COMPLETED" }
# -----------------------------
@jwt_required()
def doctor_update_appointment_status(appt_id):
    user, doctor = _get_current_doctor()
    if not doctor:
        return jsonify({"message": "Doctor not found or invalid role"}), 404

    appt = Appointment.query.filter_by(id=appt_id, doctor_id=doctor.id).first()
    if not appt:
        return jsonify({"message": "Appointment not found"}), 404

    data = request.get_json() or {}
    new_status = (data.get("status") or "").upper()
    if new_status not in {"BOOKED", "COMPLETED", "CANCELLED"}:
        return jsonify({"message": "Invalid status"}), 400

    appt.status = new_status
    db.session.commit()

    return jsonify({"message": "Status updated", "status": appt.status}), 200


# -----------------------------
# POST /api/doctor/appointments/<appt_id>/treatment
#
# Body example:
# {
#   "visit_type": "IN_PERSON" | "ONLINE",
#   "tests": ["CBC", "ECG"],
#   "diagnosis": "Acute gastritis",
#   "medicines": [
#       { "name": "DOLO650", "pattern": "1-1-1" },
#       { "name": "PAN40", "pattern": "1-0-1" }
#   ],
#   "precautions": "Drink water; avoid outside food.",
#   "notes": "Any extra notes...",
#   "follow_up_date": "2025-12-01"   # optional
# }
#
# We *encode* this into Treatment:
#   prescription: "DOLO650-1-1-1 | PAN40-1-0-1"
#   notes: "Tests done: CBC, ECG | Visit type: IN_PERSON | Precautions: ... | Follow up: 2025-12-01 | Extra: ..."
# -----------------------------
@jwt_required()
def doctor_save_treatment(appt_id):
    user, doctor = _get_current_doctor()
    if not doctor:
        return jsonify({"message": "Doctor not found or invalid role"}), 404

    appt = Appointment.query.filter_by(id=appt_id, doctor_id=doctor.id).first()
    if not appt:
        return jsonify({"message": "Appointment not found"}), 404

    data = request.get_json() or {}

    diagnosis = (data.get("diagnosis") or "").strip() or None
    visit_type = (data.get("visit_type") or "").strip() or None
    precautions = (data.get("precautions") or "").strip() or None
    extra_notes = (data.get("notes") or "").strip() or None
    follow_up_date = (data.get("follow_up_date") or "").strip() or None

    # tests can be list or comma string
    tests_field = data.get("tests")
    tests_list = []
    if isinstance(tests_field, list):
        tests_list = [str(t).strip() for t in tests_field if str(t).strip()]
    elif isinstance(tests_field, str):
        tests_list = [s.strip() for s in tests_field.split(",") if s.strip()]

    tests_text = ", ".join(tests_list) if tests_list else None

    # medicines to prescription string "NAME-1-0-1 | NAME2-0-0-1"
    meds_field = data.get("medicines") or []
    med_chunks = []
    for m in meds_field:
        name = (m.get("name") or "").strip()
        pattern = (m.get("pattern") or "").strip()
        if not name:
            continue
        if pattern:
            med_chunks.append(f"{name}-{pattern}")
        else:
            med_chunks.append(name)
    prescription = " | ".join(med_chunks) if med_chunks else None

    notes_parts = []
    if tests_text:
        notes_parts.append(f"Tests done: {tests_text}")
    if visit_type:
        notes_parts.append(f"Visit type: {visit_type}")
    if precautions:
        notes_parts.append(f"Precautions: {precautions}")
    if follow_up_date:
        notes_parts.append(f"Follow up: {follow_up_date}")
    if extra_notes:
        notes_parts.append(f"Extra: {extra_notes}")

    notes_combined = " | ".join(notes_parts) if notes_parts else None

    # create or update latest treatment
    treatment = None
    if appt.treatments:
        # overwrite latest one
        treatment = max(appt.treatments, key=lambda t: t.created_at or datetime.min)

    if not treatment:
        treatment = Treatment(appointment=appt)

    treatment.diagnosis = diagnosis
    treatment.prescription = prescription
    treatment.notes = notes_combined
    treatment.created_at = datetime.utcnow()

    db.session.add(treatment)

    # mark appointment as COMPLETED by default when saving treatment
    appt.status = "COMPLETED"

    db.session.commit()

    return jsonify({
        "message": "Treatment saved successfully",
        "status": appt.status,
    }), 200


# -----------------------------
# GET /api/doctor/patient-history/<patient_id>
#
# → Same shape as patient /history but filtered to this doctor + patient.
# -----------------------------
@jwt_required()
def doctor_patient_history(patient_id):
    user, doctor = _get_current_doctor()
    if not doctor:
        return jsonify({"message": "Doctor not found or invalid role"}), 404

    # ensure patient exists
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"message": "Patient not found"}), 404

    appts = (
        Appointment.query
        .filter_by(doctor_id=doctor.id, patient_id=patient.id)
        .order_by(Appointment.date.desc(), Appointment.created_at.desc())
        .all()
    )

    history = []
    for a in appts:
        item = a.to_patient_dict()
        # attach simple treatment info
        if a.treatments:
            latest_t = max(a.treatments, key=lambda x: x.created_at or datetime.min)
            item["treatment"] = {
                "id": latest_t.id,
                "diagnosis": latest_t.diagnosis,
                "prescription": latest_t.prescription,
                "notes": latest_t.notes,
                "created_at": latest_t.created_at.isoformat() if latest_t.created_at else None,
            }
        else:
            item["treatment"] = None
        history.append(item)

    return jsonify({
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
        },
        "history": history,
    }), 200


# -----------------------------
# GET /api/doctor/availability?days=7
#
# → Red/green grid for doctor view (read-only)
# -----------------------------
@jwt_required()
def doctor_availability():
    user, doctor = _get_current_doctor()
    if not doctor:
        return jsonify({"message": "Doctor not found or invalid role"}), 404

    days = request.args.get("days", type=int) or 7
    if days < 1:
        days = 1
    if days > 30:
        days = 30

    today = date.today()
    start_date = today
    end_date = today + timedelta(days=days - 1)

    # working hours as in patient_available_slots
    start_time = dtime(9, 0)
    end_time = dtime(17, 0)

    # fetch all non-cancelled appts in this window
    appts = (
        Appointment.query
        .filter_by(doctor_id=doctor.id)
        .filter(Appointment.status != "CANCELLED")
        .filter(Appointment.date >= start_date.strftime("%Y-%m-%d"))
        .filter(Appointment.date <= end_date.strftime("%Y-%m-%d"))
        .all()
    )

    booked_map = {}  # date_str -> set(times)
    for a in appts:
        booked_map.setdefault(a.date, set()).add(a.time)

    days_payload = []

    for i in range(days):
        d = start_date + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")

        slots = []
        current_dt = datetime.combine(d, start_time)
        end_dt = datetime.combine(d, end_time)
        while current_dt < end_dt:
            t_str = current_dt.strftime("%H:%M")
            is_booked = t_str in booked_map.get(date_str, set())
            slots.append({
                "time": t_str,
                "status": "booked" if is_booked else "free",
            })
            current_dt += timedelta(minutes=30)

        days_payload.append({
            "date": date_str,
            "slots": slots,
        })

    return jsonify({"days": days_payload}), 200
