# routes/patient_routes.py

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, time, timedelta

from models import db, User, Patient, Doctor, Appointment, Treatment


# -----------------------------------
# Helper: get current patient + user
# -----------------------------------
def _get_current_patient():
    """
    Resolves the current JWT user and ensures they are a patient.
    Uses 1–1 mapping: Patient.id == User.id
    """
    user_id = get_jwt_identity()
    if not user_id:
        return None, None

    user = User.query.get(user_id)
    if not user or user.role != "patient":
        return None, None

    patient = Patient.query.get(user_id)
    return user, patient


# -----------------------------------
# GET /api/patient/profile
#   → Patient dashboard & profile page
#   Logic w.r.t Admin/Doctor:
#   - Admin can change user.email/username/is_active in separate admin routes.
#   - Patient can see latest email/username as stored on User.
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
#   Logic w.r.t Admin/Doctor:
#   - Admin may also edit Patient in separate admin routes if needed.
#   - Doctors only read this data; they never modify patient profile.
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
            patient.height_cm = float(data["height_cm"]) if data["height_cm"] is not None else None
        except (TypeError, ValueError):
            pass

    if "weight_kg" in data:
        try:
            patient.weight_kg = float(data["weight_kg"]) if data["weight_kg"] is not None else None
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
#   Logic w.r.t Admin/Doctor:
#   - Only doctors with User.is_active = True are shown.
#   - If admin deactivates a doctor (is_active=False), they instantly
#     disappear from patient side and cannot be booked anymore.
# -----------------------------------
@jwt_required()
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
    return jsonify(result), 200


# -----------------------------------
# GET /api/patient/available-slots?doctor_id=&date=YYYY-MM-DD
#
#   → Returns slots with status: "free" / "booked"
#
#   Logic w.r.t Admin/Doctor:
#   - Only active doctors (User.is_active=True) are considered.
#   - Any appointment with status != "CANCELLED" blocks that slot.
#     So if doctor/admin marks appointment COMPLETED or still BOOKED,
#     that slot is busy.
#   - If doctor/admin cancels an appointment (status="CANCELLED"),
#     this slot becomes free again.
# -----------------------------------
@jwt_required()
def patient_available_slots():
    doctor_id = request.args.get("doctor_id", type=int)
    date_str = request.args.get("date")

    if not doctor_id or not date_str:
        return jsonify({"message": "doctor_id and date are required"}), 400

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
        return jsonify({"message": "Doctor not found or inactive"}), 404

    # Validate date
    try:
        appt_date = datetime.fromisoformat(date_str).date()
    except Exception:
        return jsonify({"message": "Invalid date format"}), 400

    # Optional: disallow past dates
    if appt_date < date.today():
        return jsonify({"message": "Date cannot be in the past"}), 400

    # Working hours 09:00–17:00, 30-min slots, "HH:MM"
    start_time = time(9, 0)
    end_time = time(17, 0)

    slots = []
    current_dt = datetime.combine(appt_date, start_time)
    end_dt = datetime.combine(appt_date, end_time)
    while current_dt < end_dt:
        slots.append(current_dt.strftime("%H:%M"))  # "10:00"
        current_dt += timedelta(minutes=30)

    # Appointments that block slots
    booked = (
        Appointment.query
        .filter_by(doctor_id=doctor.id, date=date_str)
        .filter(Appointment.status != "CANCELLED")
        .all()
    )
    booked_slots = {a.time for a in booked}

    # Include status for red/green UI
    detailed_slots = [
        {
            "time": s,
            "status": "booked" if s in booked_slots else "free",
        }
        for s in slots
    ]

    return jsonify({"slots": detailed_slots}), 200


# -----------------------------------
# GET /api/patient/appointments
#   → List all appointments for logged-in patient.
#
#   Logic w.r.t Admin/Doctor:
#   - Doctors & admins may update Appointment.status (BOOKED/COMPLETED/CANCELLED)
#     in their own routes; patient just sees the final state here.
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

    # Use helper so patient gets doctor_name + specialization, etc.
    result = [a.to_patient_dict() for a in appts]
    return jsonify(result), 200


# -----------------------------------
# GET /api/patient/appointments/<appointment_id>
#   → Detailed view for a single appointment.
#
#   Logic:
#   - Patient can only see appointments that belong to them.
#   - Doctors/admins can have separate detailed endpoints if needed.
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
#
#   Logic w.r.t Admin/Doctor:
#   - Only active doctors can be booked (User.is_active=True).
#   - If admin later deactivates a doctor, existing appointments
#     still exist, but new bookings cannot be created.
#   - Slot conflict:
#       If another patient books the same doctor/date/time and
#       doctor/admin doesn't cancel it, slot is blocked.
# -----------------------------------
@jwt_required()
def create_patient_appointment():
    user, patient = _get_current_patient()
    if not patient:
        return jsonify({"message": "Patient not found or invalid role"}), 404

    data = request.get_json() or {}

    doctor_id = data.get("doctor_id")
    date_str = data.get("appointment_date")  # "YYYY-MM-DD"
    time_slot = data.get("time_slot")        # "HH:MM" or formatted
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

    return jsonify({
        "message": "Appointment booked successfully",
        "appointment": appt.to_patient_dict(),
    }), 201


# -----------------------------------
# POST /api/patient/appointments/<appointment_id>/cancel
#
#   Logic w.r.t Admin/Doctor:
#   - Patient can cancel only their own appointments.
#   - You may decide business rules:
#       * Disallow cancelling COMPLETED ones.
#       * Optionally disallow cancelling past dates.
#   - Once cancelled, slot becomes free again in available-slots.
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

    # Example stricter rules:
    #  - don't allow cancelling COMPLETED appointments
    try:
        appt_date = datetime.fromisoformat(appt.date).date()
    except Exception:
        appt_date = None

    if appt.status == "COMPLETED":
        return jsonify({"message": "Cannot cancel a completed appointment"}), 400

    # Optional: restrict cancelling past appointments at all
    if appt_date and appt_date < date.today():
        return jsonify({"message": "Cannot cancel past appointments"}), 400

    appt.status = "CANCELLED"
    db.session.commit()

    return jsonify({"message": "Appointment cancelled successfully"}), 200


# -----------------------------------
# GET /api/patient/history
#
#   → Visit history for patient including treatments.
#
#   Logic w.r.t Admin/Doctor:
#   - Doctor endpoints will create Treatment rows and mark appointment
#     status as COMPLETED when consultation is done.
#   - Patient here only reads combined info: appointment + latest treatment.
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

            # optional: full treatment history for that appointment
            item["all_treatments"] = [t.to_dict() for t in a.treatments]
        else:
            item["treatment"] = None
            item["all_treatments"] = []

        history.append(item)

    return jsonify(history), 200
