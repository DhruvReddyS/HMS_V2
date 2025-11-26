from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import or_
from models import db, User, Doctor, Patient, Appointment


# ---------- Helper: verify admin ----------
def _require_admin():
    claims = get_jwt()                       # JWT claims
    role = claims.get("role")                # read role from claims

    if role != "admin":
        return False, jsonify({"message": "Admin access required"}), 403

    user_id = get_jwt_identity()             # identity is just user.id
    return True, {"id": user_id, "role": role}, None


# --------------------------------------
# 1. DASHBOARD STATS
# GET /api/admin/stats
# --------------------------------------
@jwt_required()
def admin_stats():
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    doctors_count = User.query.filter_by(role="doctor").count()
    patients_count = User.query.filter_by(role="patient").count()
    appointments_count = Appointment.query.count()

    return jsonify({
        "doctors": doctors_count,
        "patients": patients_count,
        "appointments": appointments_count
    })


# --------------------------------------
# 2. DOCTOR MANAGEMENT
# --------------------------------------

@jwt_required()
def create_doctor():
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    data = request.get_json() or {}

    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    specialization = data.get("specialization", "").strip()
    experience_years = data.get("experience_years", 0)
    password = data.get("password", "doctor123")

    if not full_name or not username or not email or not specialization:
        return jsonify({"message": "Missing required fields"}), 400

    existing = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing:
        return jsonify({"message": "Username or email already exists"}), 400

    user = User(
        username=username,
        email=email,
        role="doctor",
        is_active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    doctor = Doctor(
        id=user.id,
        full_name=full_name,
        specialization=specialization,
        experience_years=experience_years or 0
    )
    db.session.add(doctor)
    db.session.commit()

    return jsonify({
        "message": "Doctor created successfully",
        "doctor_id": doctor.id
    }), 201


@jwt_required()
def list_doctors():
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    search = request.args.get("search", "").strip()
    active_only = request.args.get("active_only", "false").lower() == "true"

    query = db.session.query(User, Doctor).join(Doctor, Doctor.id == User.id).filter(
        User.role == "doctor"
    )

    if active_only:
        query = query.filter(User.is_active.is_(True))

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Doctor.full_name.ilike(like_pattern),
                Doctor.specialization.ilike(like_pattern),
                User.username.ilike(like_pattern),
                User.email.ilike(like_pattern)
            )
        )

    doctors = query.all()

    result = [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_active": u.is_active,
        "full_name": d.full_name,
        "specialization": d.specialization,
        "experience_years": d.experience_years,
    } for u, d in doctors]

    return jsonify(result)


@jwt_required()
def get_doctor(doctor_id):
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    user = User.query.filter_by(id=doctor_id, role="doctor").first()
    doctor = Doctor.query.filter_by(id=doctor_id).first()

    if not user or not doctor:
        return jsonify({"message": "Doctor not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "full_name": doctor.full_name,
        "specialization": doctor.specialization,
        "experience_years": doctor.experience_years,
    })


@jwt_required()
def update_doctor(doctor_id):
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    data = request.get_json() or {}

    user = User.query.filter_by(id=doctor_id, role="doctor").first()
    doctor = Doctor.query.filter_by(id=doctor_id).first()

    if not user or not doctor:
        return jsonify({"message": "Doctor not found"}), 404

    if "email" in data:
        user.email = data["email"].strip()
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "full_name" in data:
        doctor.full_name = data["full_name"].strip()
    if "specialization" in data:
        doctor.specialization = data["specialization"].strip()
    if "experience_years" in data:
        doctor.experience_years = data["experience_years"] or 0

    db.session.commit()
    return jsonify({"message": "Doctor updated successfully"})


@jwt_required()
def delete_doctor(doctor_id):
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    user = User.query.filter_by(id=doctor_id, role="doctor").first()

    if not user:
        return jsonify({"message": "Doctor not found"}), 404

    user.is_active = False
    db.session.commit()

    return jsonify({"message": "Doctor deactivated"})


# --------------------------------------
# 3. PATIENT MANAGEMENT
# --------------------------------------

@jwt_required()
def list_patients():
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    search = request.args.get("search", "").strip()

    query = db.session.query(User, Patient).join(Patient, Patient.id == User.id).filter(
        User.role == "patient"
    )

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Patient.full_name.ilike(like_pattern),
                User.email.ilike(like_pattern),
                User.username.ilike(like_pattern),
                Patient.phone.ilike(like_pattern)
            )
        )

    records = query.all()

    result = [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_active": u.is_active,
        "full_name": p.full_name,
        "phone": p.phone,
        "address": p.address,
    } for u, p in records]

    return jsonify(result)


@jwt_required()
def get_patient(patient_id):
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    user = User.query.filter_by(id=patient_id, role="patient").first()
    pat = Patient.query.filter_by(id=patient_id).first()

    if not user or not pat:
        return jsonify({"message": "Patient not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "full_name": pat.full_name,
        "phone": pat.phone,
        "address": pat.address,
    })


@jwt_required()
def update_patient(patient_id):
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    data = request.get_json() or {}

    user = User.query.filter_by(id=patient_id, role="patient").first()
    pat = Patient.query.filter_by(id=patient_id).first()

    if not user or not pat:
        return jsonify({"message": "Patient not found"}), 404

    if "email" in data:
        user.email = data["email"].strip()
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "full_name" in data:
        pat.full_name = data["full_name"].strip()
    if "phone" in data:
        pat.phone = data["phone"].strip()
    if "address" in data:
        pat.address = data["address"].strip()

    db.session.commit()
    return jsonify({"message": "Patient updated successfully"})


@jwt_required()
def delete_patient(patient_id):
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    user = User.query.filter_by(id=patient_id, role="patient").first()

    if not user:
        return jsonify({"message": "Patient not found"}), 404

    user.is_active = False
    db.session.commit()

    return jsonify({"message": "Patient deactivated"})


# --------------------------------------
# 4. APPOINTMENT MANAGEMENT
# --------------------------------------

@jwt_required()
def admin_appointments():
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    status = request.args.get("status")
    doctor_id = request.args.get("doctor_id")
    patient_id = request.args.get("patient_id")

    query = Appointment.query

    if status:
        query = query.filter_by(status=status)
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    if patient_id:
        query = query.filter_by(patient_id=patient_id)

    appts = query.all()

    result = [{
        "id": a.id,
        "patient_id": a.patient_id,
        "doctor_id": a.doctor_id,
        "date": a.date,
        "time": a.time,
        "status": a.status,
        "created_at": a.created_at.isoformat() if getattr(a, "created_at", None) else None
    } for a in appts]

    return jsonify(result)


@jwt_required()
def admin_update_appointment_status(appointment_id):
    ok, identity, resp = _require_admin()
    if not ok:
        return resp

    data = request.get_json() or {}
    new_status = data.get("status", "").upper()

    if new_status not in ["BOOKED", "COMPLETED", "CANCELLED"]:
        return jsonify({"message": "Invalid status"}), 400

    appt = Appointment.query.get(appointment_id)
    if not appt:
        return jsonify({"message": "Appointment not found"}), 404

    appt.status = new_status
    db.session.commit()

    return jsonify({"message": "Appointment status updated"})
