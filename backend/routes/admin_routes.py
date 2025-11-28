from cache_utils import cached, cache_delete_pattern
from datetime import date, datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import or_, func

from models import db, User, Doctor, Patient, Appointment


# ---------- Helpers ----------
def _require_admin():
    """
    Ensure current JWT has role=admin.
    Returns (ok: bool, identity: dict | None, resp: flask.Response | None).
    """
    claims = get_jwt()          # JWT claims
    role = claims.get("role")   # read role from claims

    if role != "admin":
        return False, None, jsonify({"message": "Admin access required"}), 403

    user_id = get_jwt_identity()  # identity is just user.id (string/int)
    return True, {"id": int(user_id), "role": role}, None


def _calculate_age(dob_value):
    """
    Accepts a date object or a 'YYYY-MM-DD' string.
    Returns age in years (int) or None if dob is missing/invalid.
    """
    if not dob_value:
        return None

    # If it's already a date object, use directly
    if isinstance(dob_value, date):
        dob_date = dob_value
    else:
        try:
            dob_date = datetime.strptime(str(dob_value), "%Y-%m-%d").date()
        except ValueError:
            # If format is unexpected, just return None
            return None

    today = date.today()
    age = today.year - dob_date.year - (
        (today.month, today.day) < (dob_date.month, dob_date.day)
    )
    return age


# ========== 1. DASHBOARD STATS ==========

def _compute_admin_stats():
    """
    Heavy DB logic extracted so we can safely cache it.
    """
    # Aggregate doctor/patient counts in one query
    role_counts = dict(doctor=0, patient=0)
    rows = (
        db.session.query(User.role, func.count(User.id))
        .filter(User.role.in_(["doctor", "patient"]))
        .group_by(User.role)
        .all()
    )
    for role, cnt in rows:
        if role == "doctor":
            role_counts["doctor"] = cnt
        elif role == "patient":
            role_counts["patient"] = cnt

    # Total appointments
    appointments_count = db.session.query(func.count(Appointment.id)).scalar() or 0

    return {
        "doctors": role_counts["doctor"],
        "patients": role_counts["patient"],
        "appointments": appointments_count,
    }


@cached(prefix="admin_stats", ttl=60)
def _admin_stats_cached():
    # No role checks here; this is internal only
    return _compute_admin_stats()


@jwt_required()
def admin_stats():
    """
    GET /api/admin/stats
    Admin-only, cached for 60 seconds.
    """
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    # Safe: cached impl is called only after admin check
    return jsonify(_admin_stats_cached())


# ========== 2. DOCTOR MANAGEMENT ==========

@jwt_required()
def create_doctor():
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = request.get_json() or {}

    full_name = (data.get("full_name") or "").strip()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    specialization = (data.get("specialization") or "").strip()
    experience_years = data.get("experience_years", 0)
    password = data.get("password") or "doctor123"

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
        is_active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    doctor = Doctor(
        id=user.id,
        full_name=full_name,
        specialization=specialization,
        experience_years=experience_years or 0,
    )
    db.session.add(doctor)
    db.session.commit()

    # Invalidate relevant caches
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_doctors:*")
    cache_delete_pattern("API:patient_doctors:*")

    return jsonify({
        "message": "Doctor created successfully",
        "doctor_id": doctor.id,
    }), 201


def _list_doctors_impl():
    """
    Core logic for listing doctors. Called only from admin wrapper.
    """
    search = (request.args.get("search") or "").strip()
    active_only = (request.args.get("active_only") or "false").lower() == "true"

    query = (
        db.session.query(User, Doctor)
        .join(Doctor, Doctor.id == User.id)
        .filter(User.role == "doctor")
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
                User.email.ilike(like_pattern),
            )
        )

    doctors = query.all()

    return [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_active": u.is_active,
        "full_name": d.full_name,
        "specialization": d.specialization,
        "experience_years": d.experience_years,
    } for u, d in doctors]


@cached(prefix="admin_doctors", ttl=60)
def _admin_list_doctors_cached():
    return _list_doctors_impl()


@jwt_required()
def list_doctors():
    """
    GET /api/admin/doctors
    Admin-only, cached for 60s (per search/active_only query).
    """
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    return jsonify(_admin_list_doctors_cached())


@jwt_required()
def get_doctor(doctor_id):
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

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
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = request.get_json() or {}

    user = User.query.filter_by(id=doctor_id, role="doctor").first()
    doctor = Doctor.query.filter_by(id=doctor_id).first()

    if not user or not doctor:
        return jsonify({"message": "Doctor not found"}), 404

    if "email" in data:
        user.email = (data["email"] or "").strip()
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "full_name" in data:
        doctor.full_name = (data["full_name"] or "").strip()
    if "specialization" in data:
        doctor.specialization = (data["specialization"] or "").strip()
    if "experience_years" in data:
        doctor.experience_years = data["experience_years"] or 0

    db.session.commit()

    # Invalidate relevant caches
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_doctors:*")
    cache_delete_pattern("API:patient_doctors:*")

    return jsonify({"message": "Doctor updated successfully"})


@jwt_required()
def delete_doctor(doctor_id):
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    user = User.query.filter_by(id=doctor_id, role="doctor").first()

    if not user:
        return jsonify({"message": "Doctor not found"}), 404

    user.is_active = False
    db.session.commit()

    # Invalidate relevant caches
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_doctors:*")
    cache_delete_pattern("API:patient_doctors:*")

    return jsonify({"message": "Doctor deactivated"})


# ========== 3. PATIENT MANAGEMENT ==========

@jwt_required()
def create_patient():
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = request.get_json() or {}

    full_name = (data.get("full_name") or "").strip()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()
    gender = (data.get("gender") or "").strip() or None
    dob = (data.get("dob") or "").strip() or None

    if not full_name or not username or not email:
        return jsonify({"message": "full_name, username and email are required"}), 400

    existing = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing:
        return jsonify({"message": "Username or email already exists"}), 400

    password = data.get("password") or "patient123"

    user = User(
        username=username,
        email=email,
        role="patient",
        is_active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # get user.id

    patient = Patient(
        id=user.id,
        full_name=full_name,
        phone=phone or None,
        address=address or None,
        gender=gender,
        dob=dob,
    )
    db.session.add(patient)
    db.session.commit()

    # Invalidate relevant caches
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_patients:*")

    return jsonify({
        "message": "Patient created successfully",
        "patient_id": patient.id,
    }), 201


def _list_patients_impl():
    search = (request.args.get("search") or "").strip()

    query = (
        db.session.query(User, Patient)
        .join(Patient, Patient.id == User.id)
        .filter(User.role == "patient")
    )

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Patient.full_name.ilike(like_pattern),
                User.email.ilike(like_pattern),
                User.username.ilike(like_pattern),
                Patient.phone.ilike(like_pattern),
            )
        )

    records = query.all()

    return [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_active": u.is_active,
        "full_name": p.full_name,
        "phone": p.phone,
        "address": p.address,
        "gender": p.gender,
        "dob": p.dob,
        "age": _calculate_age(p.dob),
    } for u, p in records]


@cached(prefix="admin_patients", ttl=60)
def _admin_list_patients_cached():
    return _list_patients_impl()


@jwt_required()
def list_patients():
    """
    GET /api/admin/patients
    Admin-only, cached for 60s (per search query).
    """
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    return jsonify(_admin_list_patients_cached())


@jwt_required()
def get_patient(patient_id):
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

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
        "gender": pat.gender,
        "dob": pat.dob,
        "age": _calculate_age(pat.dob),
    })


@jwt_required()
def update_patient(patient_id):
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = request.get_json() or {}

    user = User.query.filter_by(id=patient_id, role="patient").first()
    pat = Patient.query.filter_by(id=patient_id).first()

    if not user or not pat:
        return jsonify({"message": "Patient not found"}), 404

    if "email" in data:
        user.email = (data["email"] or "").strip()
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "full_name" in data:
        pat.full_name = (data["full_name"] or "").strip()
    if "phone" in data:
        pat.phone = (data["phone"] or "").strip()
    if "address" in data:
        pat.address = (data["address"] or "").strip()
    if "gender" in data:
        pat.gender = (data["gender"] or "").strip() or None
    if "dob" in data:
        pat.dob = (data["dob"] or "").strip() or None

    db.session.commit()

    # Invalidate relevant caches
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_patients:*")

    return jsonify({"message": "Patient updated successfully"})


@jwt_required()
def delete_patient(patient_id):
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    user = User.query.filter_by(id=patient_id, role="patient").first()

    if not user:
        return jsonify({"message": "Patient not found"}), 404

    user.is_active = False
    db.session.commit()

    # Invalidate relevant caches
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_patients:*")

    return jsonify({"message": "Patient deactivated"})


# ========== 4. APPOINTMENT MANAGEMENT ==========

def _admin_appointments_impl():
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

    return [{
        "id": a.id,
        "patient_id": a.patient_id,
        "doctor_id": a.doctor_id,
        "date": a.date,
        "time": a.time,
        "status": a.status,
        "created_at": a.created_at.isoformat() if getattr(a, "created_at", None) else None,
    } for a in appts]


@cached(prefix="admin_appointments", ttl=30)
def _admin_appointments_cached():
    return _admin_appointments_impl()


@jwt_required()
def admin_appointments():
    """
    GET /api/admin/appointments
    Admin-only, cached for 30s (per filter combination).
    """
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    return jsonify(_admin_appointments_cached())


@jwt_required()
def admin_update_appointment_status(appointment_id):
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = request.get_json() or {}
    new_status = (data.get("status") or "").upper()

    if new_status not in ["BOOKED", "COMPLETED", "CANCELLED"]:
        return jsonify({"message": "Invalid status"}), 400

    appt = Appointment.query.get(appointment_id)
    if not appt:
        return jsonify({"message": "Appointment not found"}), 404

    appt.status = new_status
    db.session.commit()

    # Invalidate caches affected by appointment changes
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({"message": "Appointment status updated"})
