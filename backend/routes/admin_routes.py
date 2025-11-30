from cache_utils import cached, cache_delete_pattern
from datetime import date, datetime
from flask import request, jsonify, send_file, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import or_, func
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from models import db, User, Doctor, Patient, Appointment


def _require_admin():
    claims = get_jwt()
    role = claims.get("role")

    if role != "admin":
        return False, None, jsonify({"message": "Admin access required"}), 403

    user_id = get_jwt_identity()
    identity = {"id": int(user_id), "role": role}
    return True, identity, None, None


def _calculate_age(dob_value):
    if not dob_value:
        return None

    if isinstance(dob_value, date):
        dob_date = dob_value
    else:
        try:
            dob_date = datetime.strptime(str(dob_value), "%Y-%m-%d").date()
        except ValueError:
            return None

    today = date.today()
    age = today.year - dob_date.year - (
        (today.month, today.day) < (dob_date.month, dob_date.day)
    )
    return age


def _compute_month_range(year: int, month: int):
    start_str = f"{year:04d}-{month:02d}-01"

    if month == 12:
        end_str = f"{year + 1:04d}-01-01"
    else:
        end_str = f"{year:04d}-{month + 1:02d}-01"

    return start_str, end_str


def _compute_monthly_report(year: int, month: int):
    start_date, end_date = _compute_month_range(year, month)

    base_q = Appointment.query.filter(
        Appointment.date >= start_date,
        Appointment.date < end_date,
    )

    booked = base_q.filter(Appointment.status == "BOOKED").count()
    completed = base_q.filter(Appointment.status == "COMPLETED").count()
    cancelled = base_q.filter(Appointment.status == "CANCELLED").count()

    rows = (
        db.session.query(
            Doctor.id,
            Doctor.full_name,
            Doctor.specialization,
            func.count(Appointment.id).label("completed_count"),
        )
        .join(Appointment, Appointment.doctor_id == Doctor.id)
        .filter(
            Appointment.status == "COMPLETED",
            Appointment.date >= start_date,
            Appointment.date < end_date,
        )
        .group_by(Doctor.id, Doctor.full_name, Doctor.specialization)
        .order_by(func.count(Appointment.id).desc())
        .limit(5)
        .all()
    )

    top_doctors = [
        {
            "id": d_id,
            "name": full_name,
            "specialization": specialization,
            "completed": completed_count,
        }
        for d_id, full_name, specialization, completed_count in rows
    ]

    return {
        "booked": booked,
        "completed": completed,
        "cancelled": cancelled,
        "top_doctors": top_doctors,
    }


def _compute_admin_stats():
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

    appointments_count = db.session.query(func.count(Appointment.id)).scalar() or 0

    today = date.today()
    month_report = _compute_monthly_report(today.year, today.month)

    return {
        "doctors": role_counts["doctor"],
        "patients": role_counts["patient"],
        "appointments": appointments_count,
        "report": month_report,
    }


@cached(prefix="admin_stats_v2", ttl=60)
def _admin_stats_cached():
    return _compute_admin_stats()


@jwt_required()
def admin_stats():
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = _admin_stats_cached()
    if isinstance(data, Response):
        return data
    return jsonify(data), 200


def _admin_reports_analytics_impl():
    month_str = (request.args.get("month") or "").strip()
    today = date.today()
    try:
        if month_str:
            year, month = month_str.split("-")
            year = int(year)
            month = int(month)
        else:
            year, month = today.year, today.month
    except Exception:
        year, month = today.year, today.month

    start_str, end_str = _compute_month_range(year, month)

    appts = Appointment.query.filter(
        Appointment.date >= start_str,
        Appointment.date < end_str,
    ).all()

    daily_map = {}

    for a in appts:
        if isinstance(a.date, date):
            d_str = a.date.strftime("%Y-%m-%d")
        else:
            d_str = str(a.date)

        if d_str not in daily_map:
            daily_map[d_str] = {"BOOKED": 0, "COMPLETED": 0, "CANCELLED": 0}

        status = (a.status or "").upper()
        if status in daily_map[d_str]:
            daily_map[d_str][status] += 1

    daily_appointments = []
    for d_str in sorted(daily_map.keys()):
        counts = daily_map[d_str]
        daily_appointments.append({
            "date": d_str,
            "booked": counts["BOOKED"],
            "completed": counts["COMPLETED"],
            "cancelled": counts["CANCELLED"],
        })

    status_counts = {
        "BOOKED": sum(x["booked"] for x in daily_appointments),
        "COMPLETED": sum(x["completed"] for x in daily_appointments),
        "CANCELLED": sum(x["cancelled"] for x in daily_appointments),
    }

    spec_rows = (
        db.session.query(
            Doctor.specialization,
            func.count(Appointment.id).label("cnt"),
        )
        .join(Appointment, Appointment.doctor_id == Doctor.id)
        .filter(
            Appointment.date >= start_str,
            Appointment.date < end_str,
        )
        .group_by(Doctor.specialization)
        .all()
    )

    specialization_counts = [
        {
            "specialization": spec or "Unknown",
            "appointments": cnt,
        }
        for spec, cnt in spec_rows
    ]

    doc_rows = (
        db.session.query(
            Doctor.id,
            Doctor.full_name,
            Doctor.specialization,
            func.count(Appointment.id).label("completed_cnt"),
        )
        .join(Appointment, Appointment.doctor_id == Doctor.id)
        .filter(
            Appointment.status == "COMPLETED",
            Appointment.date >= start_str,
            Appointment.date < end_str,
        )
        .group_by(Doctor.id, Doctor.full_name, Doctor.specialization)
        .order_by(func.count(Appointment.id).desc())
        .limit(10)
        .all()
    )

    doctor_productivity = [
        {
            "doctor_id": d_id,
            "name": full_name,
            "specialization": spec,
            "completed": completed_cnt,
        }
        for d_id, full_name, spec, completed_cnt in doc_rows
    ]

    return {
        "month": f"{year:04d}-{month:02d}",
        "daily_appointments": daily_appointments,
        "status_counts": status_counts,
        "specialization_counts": specialization_counts,
        "doctor_productivity": doctor_productivity,
    }


@cached(prefix="admin_reports_analytics", ttl=60)
def _admin_reports_analytics_cached():
    return _admin_reports_analytics_impl()


@jwt_required()
def admin_reports_analytics():
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = _admin_reports_analytics_cached()
    if isinstance(data, Response):
        return data
    return jsonify(data), 200


@jwt_required()
def admin_monthly_report():
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    month_str = (request.args.get("month") or "").strip()
    today = date.today()

    try:
        if month_str:
            year, month = month_str.split("-")
            year = int(year)
            month = int(month)
        else:
            year, month = today.year, today.month
    except Exception:
        year, month = today.year, today.month

    report = _compute_monthly_report(year, month)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    title = f"Hospital Monthly Report - {year}-{month:02d}"
    y = height - 80

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, title)
    y -= 40

    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Booked appointments   : {report['booked']}")
    y -= 20
    p.drawString(50, y, f"Completed appointments: {report['completed']}")
    y -= 20
    p.drawString(50, y, f"Cancelled appointments: {report['cancelled']}")
    y -= 30

    total = report["booked"] + report["completed"] + report["cancelled"]
    p.drawString(50, y, f"Total appointments     : {total}")
    y -= 40

    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "Top Performing Doctors")
    y -= 25

    p.setFont("Helvetica", 11)
    if not report["top_doctors"]:
        p.drawString(60, y, "No completed appointments data found for this month.")
        y -= 20
    else:
        for doc in report["top_doctors"]:
            line = f"{doc['name']} ({doc['specialization']}) - {doc['completed']} completed"
            p.drawString(60, y, line)
            y -= 18
            if y < 80:
                p.showPage()
                y = height - 80
                p.setFont("Helvetica", 11)

    p.showPage()
    p.save()
    buffer.seek(0)

    filename = f"hospital_report_{year}-{month:02d}.pdf"
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


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

    cache_delete_pattern("API:admin_stats_v2:*")
    cache_delete_pattern("API:admin_doctors:*")
    cache_delete_pattern("API:patient_doctors:*")
    cache_delete_pattern("API:admin_reports_analytics:*")

    return jsonify({
        "message": "Doctor created successfully",
        "doctor_id": doctor.id,
    }), 201


def _list_doctors_impl():
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
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = _admin_list_doctors_cached()
    if isinstance(data, Response):
        return data
    return jsonify(data), 200


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
    }), 200


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

    cache_delete_pattern("API:admin_stats_v2:*")
    cache_delete_pattern("API:admin_doctors:*")
    cache_delete_pattern("API:patient_doctors:*")
    cache_delete_pattern("API:admin_reports_analytics:*")

    return jsonify({"message": "Doctor updated successfully"}), 200


@jwt_required()
def delete_doctor(doctor_id):
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    user = User.query.filter_by(id=doctor_id, role="doctor").first()
    if not user:
        return jsonify({"message": "Doctor not found"}), 404

    db.session.delete(user)
    db.session.commit()

    cache_delete_pattern("API:admin_stats_v2:*")
    cache_delete_pattern("API:admin_doctors:*")
    cache_delete_pattern("API:patient_doctors:*")
    cache_delete_pattern("API:admin_reports_analytics:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({"message": "Doctor deleted permanently"}), 200


@jwt_required()
def create_patient():
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = request.get_json() or{}

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
    db.session.flush()

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

    cache_delete_pattern("API:admin_stats_v2:*")
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
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = _admin_list_patients_cached()
    if isinstance(data, Response):
        return data
    return jsonify(data), 200


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
    }), 200


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

    cache_delete_pattern("API:admin_stats_v2:*")
    cache_delete_pattern("API:admin_patients:*")

    return jsonify({"message": "Patient updated successfully"}), 200


@jwt_required()
def delete_patient(patient_id):
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    user = User.query.filter_by(id=patient_id, role="patient").first()
    if not user:
        return jsonify({"message": "Patient not found"}), 404

    db.session.delete(user)
    db.session.commit()

    cache_delete_pattern("API:admin_stats_v2:*")
    cache_delete_pattern("API:admin_patients:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")
    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")

    return jsonify({"message": "Patient deleted permanently"}), 200


def _admin_appointments_impl():
    status = request.args.get("status")
    doctor_id = request.args.get("doctor_id")
    patient_id = request.args.get("patient_id")
    appointment_id = request.args.get("id")

    query = Appointment.query

    if appointment_id:
        try:
            appt_id_int = int(appointment_id)
        except ValueError:
            return []
        query = query.filter_by(id=appt_id_int)

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
    ok, identity, resp, status = _require_admin()
    if not ok:
        return resp, status

    data = _admin_appointments_cached()
    if isinstance(data, Response):
        return data
    return jsonify(data), 200


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

    cache_delete_pattern("API:admin_stats_v2:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:admin_reports_analytics:*")
    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({"message": "Appointment status updated"}), 200
