from datetime import datetime, date, timedelta
from calendar import monthrange
import csv
from flask import request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import or_
import io
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from cache_utils import cached, cache_delete_pattern
from models import (
    db,
    User,
    Doctor,
    Patient,
    Appointment,
    Treatment,
    DoctorAvailability,
)


def _today() -> date:
    return date.today()


def _iso(d: date) -> str:
    return d.isoformat() if d else None


def _parse_date_param(name, default_today: bool = True) -> date | None:
    value = request.args.get(name)
    if not value:
        return _today() if default_today else None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return _today() if default_today else None


def _require_doctor_role():
    claims = get_jwt()
    role = claims.get("role")
    if role != "doctor":
        return False, jsonify({"message": "Doctor access required"}), 403
    return True, None, None


def _get_doctor_id() -> int:
    return int(get_jwt_identity())


DEFAULT_TIME_SLOTS = [
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
]


def _calc_age(dob) -> int | None:
    if not dob:
        return None

    if isinstance(dob, str):
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            return None
    elif isinstance(dob, date):
        dob_date = dob
    else:
        try:
            dob_date = dob.date()
        except Exception:
            return None

    today = _today()
    years = today.year - dob_date.year
    if (today.month, today.day) < (dob_date.month, dob_date.day):
        years -= 1
    return years


@jwt_required()
@cached(prefix="doctor_dashboard", ttl=60)
def doctor_dashboard_summary():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    user = User.query.get(user_id)
    doctor_profile = Doctor.query.get(user_id)

    today = _today()
    today_str = today.isoformat()

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    week_start_str = week_start.isoformat()
    week_end_str = week_end.isoformat()

    todays_appts = (
        Appointment.query
        .filter(
            Appointment.doctor_id == user_id,
            Appointment.date == today_str,
        )
        .order_by(Appointment.time.asc())
        .all()
    )

    today_total = len(todays_appts)
    today_booked = sum(1 for a in todays_appts if (a.status or "").upper() == "BOOKED")
    today_completed = sum(1 for a in todays_appts if (a.status or "").upper() == "COMPLETED")
    pending_visits = today_booked

    week_completed = (
        Appointment.query
        .filter(
            Appointment.doctor_id == user_id,
            Appointment.date.between(week_start_str, week_end_str),
            Appointment.status == "COMPLETED",
        )
        .count()
    )

    recent_appts = (
        Appointment.query
        .filter(Appointment.doctor_id == user_id)
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .limit(50)
        .all()
    )

    last_visits: dict[int, str] = {}
    for appt in recent_appts:
        if not appt.patient_id or not appt.date:
            continue
        pid = appt.patient_id
        if pid not in last_visits or appt.date > last_visits[pid]:
            last_visits[pid] = appt.date

    patient_ids = set(last_visits.keys())
    patient_ids.update(a.patient_id for a in todays_appts if a.patient_id)

    patient_by_id: dict[int, Patient] = {}
    if patient_ids:
        patient_by_id = {
            p.id: p
            for p in Patient.query.filter(Patient.id.in_(patient_ids)).all()
        }

    assigned_patients = sorted(
        [
            {
                "patient_id": pid,
                "full_name": (
                    patient_by_id.get(pid).full_name
                    if patient_by_id.get(pid) else f"Patient #{pid}"
                ),
                "last_visit": last_visits[pid],
            }
            for pid in last_visits.keys()
        ],
        key=lambda x: x["last_visit"],
        reverse=True,
    )[:10]

    todays_ids = [a.id for a in todays_appts]
    treated_ids = set()
    if todays_ids:
        treat_rows = Treatment.query.filter(
            Treatment.appointment_id.in_(todays_ids)
        ).all()
        treated_ids = {t.appointment_id for t in treat_rows}

    upcoming_appointments = []
    for a in todays_appts:
        p = patient_by_id.get(a.patient_id) if a.patient_id else None
        patient_name = (
            p.full_name
            if p else (f"Patient #{a.patient_id}" if a.patient_id else "Patient")
        )

        upcoming_appointments.append(
            {
                "id": a.id,
                "appointment_date": a.date,
                "time_slot": a.time,
                "status": a.status,
                "reason": a.reason,
                "patient_id": a.patient_id,
                "patient_name": patient_name,
                "has_treatment": a.id in treated_ids,
            }
        )

    doctor_payload = {
        "id": user.id if user else None,
        "full_name": getattr(doctor_profile, "full_name", None)
        or getattr(user, "username", None),
        "specialization": getattr(doctor_profile, "specialization", None),
    }

    return {
        "today": today_str,
        "doctor": doctor_payload,
        "stats": {
            "today_total": today_total,
            "today_booked": today_booked,
            "today_completed": today_completed,
            "pending_visits": pending_visits,
            "week_completed": week_completed,
            "assigned_patients": len(assigned_patients),
        },
        "upcoming_appointments": upcoming_appointments,
        "assigned_patients": assigned_patients,
    }


@jwt_required()
@cached(prefix="doctor_appointments", ttl=30)
def doctor_list_appointments():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()

    q_date = request.args.get("date")
    q_status = request.args.get("status")
    q_search = request.args.get("search")

    query = Appointment.query.filter(Appointment.doctor_id == user_id)

    if q_date:
        query = query.filter(Appointment.date == q_date)

    if q_status:
        query = query.filter(Appointment.status == q_status)

    if q_search:
        search = f"%{q_search.strip()}%"
        query = (
            query.join(Patient, Patient.id == Appointment.patient_id, isouter=True)
            .filter(
                or_(
                    Patient.full_name.ilike(search),
                    Appointment.reason.ilike(search),
                    Patient.id.cast(db.String).ilike(search),
                )
            )
        )

    appts = query.order_by(
        Appointment.date.desc(),
        Appointment.time.asc(),
    ).all()

    patient_ids = {a.patient_id for a in appts if a.patient_id}
    patients: dict[int, Patient] = {}
    if patient_ids:
        patients = {
            p.id: p for p in Patient.query.filter(Patient.id.in_(patient_ids)).all()
        }

    appt_ids = [a.id for a in appts]
    treated_ids = set()
    if appt_ids:
        treat_rows = Treatment.query.filter(
            Treatment.appointment_id.in_(appt_ids)
        ).all()
        treated_ids = {t.appointment_id for t in treat_rows}

    def _to_dict(a: Appointment):
        p = patients.get(a.patient_id)
        name = p.full_name if p else (f"Patient #{a.patient_id}" if a.patient_id else "Patient")
        return {
            "id": a.id,
            "appointment_date": a.date,
            "time_slot": a.time,
            "status": a.status,
            "reason": a.reason,
            "patient_id": a.patient_id,
            "patient_name": name,
            "has_treatment": a.id in treated_ids,
        }

    return {"appointments": [_to_dict(a) for a in appts]}


@jwt_required()
def doctor_update_appointment_status(appointment_id):
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    appt = Appointment.query.get_or_404(appointment_id)

    if appt.doctor_id != user_id:
        return jsonify({"message": "You are not allowed to modify this appointment."}), 403

    data = request.get_json() or {}
    new_status = (data.get("status") or "").upper()

    if new_status not in {"BOOKED", "COMPLETED", "CANCELLED"}:
        return jsonify({"message": "Invalid status value."}), 400

    if appt.status == "COMPLETED" and new_status == "BOOKED":
        return jsonify({"message": "Completed visits cannot be set back to BOOKED."}), 400
    if appt.status == "CANCELLED" and new_status == "BOOKED":
        return jsonify({"message": "Cancelled visits cannot be set back to BOOKED."}), 400
    if appt.status == new_status:
        return jsonify({"message": f"Appointment is already {new_status}."}), 400

    appt.status = new_status
    db.session.commit()

    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:doctor_patient_history:*")
    cache_delete_pattern("API:doctor_stats:*")
    cache_delete_pattern("API:doctor_my_patients:*")
    cache_delete_pattern("API:admin_stats_v2:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:admin_reports_analytics:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({"message": "Status updated successfully.", "status": new_status})


@jwt_required()
def doctor_save_treatment(appointment_id):
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    appt = Appointment.query.get_or_404(appointment_id)

    if appt.doctor_id != user_id:
        return jsonify({"message": "You are not allowed to modify this appointment."}), 403

    data = request.get_json() or {}

    follow_up_date = data.get("follow_up_date") or None
    if follow_up_date:
        try:
            datetime.strptime(follow_up_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"message": "Invalid follow_up_date format, expected YYYY-MM-DD."}), 400

    visit_type = data.get("visit_type")
    tests_text = data.get("tests_done") or data.get("tests")
    diagnosis = data.get("diagnosis")
    medicines_text = data.get("medicines")
    precautions = data.get("precautions")
    notes = data.get("notes")

    treatment = Treatment.query.filter_by(appointment_id=appt.id).first()
    if not treatment:
        treatment = Treatment(appointment_id=appt.id)
        db.session.add(treatment)

    treatment.visit_type = visit_type
    treatment.tests_text = tests_text
    treatment.diagnosis = diagnosis
    treatment.prescription = medicines_text
    treatment.precautions = precautions
    treatment.notes = notes
    treatment.follow_up_date = follow_up_date

    if (appt.status or "").upper() == "BOOKED":
        appt.status = "COMPLETED"

    db.session.commit()

    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:doctor_patient_history:*")
    cache_delete_pattern("API:doctor_treatment:*")
    cache_delete_pattern("API:doctor_stats:*")
    cache_delete_pattern("API:doctor_my_patients:*")
    cache_delete_pattern("API:admin_stats_v2:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:admin_reports_analytics:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")

    return jsonify({"message": "Treatment details saved successfully."})


@jwt_required()
@cached(prefix="doctor_treatment", ttl=120)
def doctor_get_treatment(appointment_id):
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    appt = Appointment.query.get_or_404(appointment_id)

    if appt.doctor_id != user_id:
        return jsonify({"message": "You are not allowed to view this appointment."}), 403

    t = Treatment.query.filter_by(appointment_id=appt.id).first()
    if not t:
        return {"exists": False, "treatment": None}

    treatment_payload = {
        "id": t.id,
        "visit_type": t.visit_type or "",
        "tests_text": t.tests_text or "",
        "diagnosis": t.diagnosis or "",
        "medicines_text": t.prescription or "",
        "precautions": t.precautions or "",
        "notes": t.notes or "",
        "follow_up_date": t.follow_up_date,
    }

    return {"exists": True, "treatment": treatment_payload}


@jwt_required()
@cached(prefix="doctor_patient_history", ttl=60)
def doctor_patient_history():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()

    patient_id = request.args.get("patient_id") or request.args.get("patientId")
    if not patient_id:
        return jsonify({"message": "patient_id query parameter is required."}), 400

    try:
        pid = int(patient_id)
    except ValueError:
        return jsonify({"message": "Invalid patient_id."}), 400

    patient = Patient.query.get(pid)
    if not patient:
        return jsonify({"message": "Patient not found."}), 404

    appts = (
        Appointment.query
        .filter(
            Appointment.doctor_id == user_id,
            Appointment.patient_id == pid,
        )
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .all()
    )

    appt_ids = [a.id for a in appts]
    treatments = []
    if appt_ids:
        treatments = Treatment.query.filter(Treatment.appointment_id.in_(appt_ids)).all()
    t_by_appt = {t.appointment_id: t for t in treatments}

    visits = []
    for a in appts:
        t = t_by_appt.get(a.id)

        tests = None
        if t and t.tests_text:
            raw = t.tests_text.replace("\r\n", "\n")
            parts: list[str] = []
            for line in raw.split("\n"):
                parts.extend([x.strip() for x in line.split(",") if x.strip()])
            tests = parts or None

        medicines = getattr(t, "prescription", None)

        visits.append(
            {
                "id": a.id,
                "appointment_date": a.date,
                "time_slot": a.time,
                "status": a.status,
                "diagnosis": getattr(t, "diagnosis", None),
                "visit_type": getattr(t, "visit_type", None),
                "tests": tests,
                "prescription": medicines,
                "medicines": medicines,
                "precautions": getattr(t, "precautions", None),
                "notes": getattr(t, "notes", None),
                "follow_up_date": getattr(t, "follow_up_date", None),
            }
        )

    patient_payload = {
        "id": patient.id,
        "patient_id": patient.id,
        "full_name": patient.full_name,
        "email": patient.user.email if patient.user else None,
        "phone": patient.phone,
        "gender": patient.gender,
        "dob": patient.dob,
        "blood_group": patient.blood_group,
    }

    return {"patient": patient_payload, "visits": visits}


@jwt_required()
@cached(prefix="doctor_availability", ttl=60)
def doctor_availability():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    start_date = _parse_date_param("start_date", default_today=True)
    end_date = start_date + timedelta(days=6)

    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    av_rows = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == user_id,
        DoctorAvailability.date.between(start_str, end_str),
    ).all()
    av_map = {(row.date, row.time_slot): row.is_available for row in av_rows}

    appts = Appointment.query.filter(
        Appointment.doctor_id == user_id,
        Appointment.date.between(start_str, end_str),
        Appointment.status != "CANCELLED",
    ).all()
    appt_map = {(a.date, a.time): a.status for a in appts if a.date and a.time}

    days = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        d_str = d.isoformat()
        slots = []

        for ts in DEFAULT_TIME_SLOTS:
            is_available = av_map.get((d_str, ts), True)
            booking_status = appt_map.get((d_str, ts))

            slots.append({
                "time_slot": ts,
                "is_available": is_available,
                "booking_status": booking_status,
            })

        days.append({"date": d_str, "slots": slots})

    return {"days": days}


@jwt_required()
def doctor_update_availability():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    data = request.get_json() or {}

    date_str = data.get("date")
    slots = data.get("slots", [])

    if not date_str:
        return jsonify({"message": "date is required"}), 400

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"message": "Invalid date"}), 400

    if not isinstance(slots, list) or len(slots) == 0:
        return jsonify({"message": "slots must be a non-empty list"}), 400

    existing_rows = DoctorAvailability.query.filter_by(
        doctor_id=user_id, date=date_str
    ).all()
    row_map = {(r.date, r.time_slot): r for r in existing_rows}

    for s in slots:
        ts = s.get("time_slot")
        is_av = s.get("is_available")

        if ts not in DEFAULT_TIME_SLOTS:
            continue
        if not isinstance(is_av, bool):
            continue

        key = (date_str, ts)
        row = row_map.get(key)
        if row:
            row.is_available = is_av
        else:
            row = DoctorAvailability(
                doctor_id=user_id, date=date_str, time_slot=ts, is_available=is_av
            )
            db.session.add(row)

    db.session.commit()

    cache_delete_pattern("API:doctor_availability:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({"message": "Availability updated successfully"})


@jwt_required()
def doctor_toggle_availability():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    data = request.get_json() or {}

    date_str = data.get("date")
    time_slot = data.get("time_slot")
    body_is_av = data.get("is_available", None)

    if not date_str or not time_slot:
        return jsonify({"message": "date and time_slot are required"}), 400

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"message": "Invalid date format, expected YYYY-MM-DD"}), 400

    if time_slot not in DEFAULT_TIME_SLOTS:
        return jsonify({"message": "Invalid time_slot for this schedule grid."}), 400

    slot = DoctorAvailability.query.filter_by(
        doctor_id=user_id,
        date=date_str,
        time_slot=time_slot,
    ).first()

    if slot:
        if isinstance(body_is_av, bool):
            slot.is_available = body_is_av
        else:
            slot.is_available = not bool(slot.is_available)
        new_val = slot.is_available
    else:
        new_val = False if body_is_av is None else bool(body_is_av)
        slot = DoctorAvailability(
            doctor_id=user_id,
            date=date_str,
            time_slot=time_slot,
            is_available=new_val,
        )
        db.session.add(slot)

    db.session.commit()

    cache_delete_pattern("API:doctor_availability:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({
        "message": "Slot updated",
        "date": date_str,
        "time_slot": time_slot,
        "is_available": new_val,
    }), 200


@jwt_required()
def doctor_get_profile():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    user = User.query.get_or_404(user_id)
    doctor = Doctor.query.get(user_id)

    full_name = doctor.full_name if (doctor and doctor.full_name) else user.username

    payload = {
        "id": user.id,
        "full_name": full_name,
        "email": user.email,
        "specialization": doctor.specialization if doctor else None,
        "experience": doctor.experience_years if doctor else None,
        "bio": doctor.about if doctor else None,
    }

    return jsonify(payload)


@jwt_required()
def doctor_update_profile():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    user = User.query.get_or_404(user_id)

    doctor = Doctor.query.get(user_id)
    if not doctor:
        doctor = Doctor(id=user_id)
        doctor.user = user
        db.session.add(doctor)

    data = request.get_json() or {}

    full_name = (data.get("full_name") or "").strip()
    specialization = (data.get("specialization") or "").strip()
    experience = data.get("experience")
    bio = (data.get("bio") or "").strip()

    if full_name:
        doctor.full_name = full_name

    doctor.specialization = specialization or None

    try:
        doctor.experience_years = int(experience) if str(experience).strip() != "" else None
    except (TypeError, ValueError):
        doctor.experience_years = None

    doctor.about = bio or None

    db.session.commit()

    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_stats:*")

    return jsonify({"message": "Profile updated successfully."})


@jwt_required()
@cached(prefix="doctor_my_patients", ttl=60)
def doctor_my_patients():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()

    appts = (
        Appointment.query
        .filter(Appointment.doctor_id == user_id)
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .all()
    )

    per_patient: dict[int, list[Appointment]] = {}
    for a in appts:
        if not a.patient_id:
            continue
        per_patient.setdefault(a.patient_id, []).append(a)

    patient_ids = list(per_patient.keys())
    if not patient_ids:
        return {"patients": []}

    patients = {
        p.id: p
        for p in Patient.query.filter(Patient.id.in_(patient_ids)).all()
    }

    result = []
    for pid, visits in per_patient.items():
        patient = patients.get(pid)
        if not patient:
            continue

        last_visit = max((a.date for a in visits if a.date), default=None)

        payload = {
            "id": patient.id,
            "full_name": patient.full_name or f"Patient #{patient.id}",
            "email": patient.user.email if patient.user else None,
            "phone": patient.phone,
            "gender": patient.gender,
            "age": _calc_age(patient.dob),
            "last_visit": last_visit,
            "total_appointments": len(visits),
        }
        result.append(payload)

    result.sort(key=lambda p: p["last_visit"] or "", reverse=True)

    return {"patients": result}


def _doctor_stats_impl():
    user_id = _get_doctor_id()
    today = _today()

    distinct_patients = (
        db.session.query(Appointment.patient_id)
        .filter(
            Appointment.doctor_id == user_id,
            Appointment.patient_id.isnot(None),
        )
        .distinct()
        .all()
    )
    total_patients = len(distinct_patients)

    first_day = date(today.year, today.month, 1)
    last_day_num = monthrange(today.year, today.month)[1]
    last_day = date(today.year, today.month, last_day_num)

    first_str = first_day.isoformat()
    last_str = last_day.isoformat()

    month_appts = (
        Appointment.query
        .filter(
            Appointment.doctor_id == user_id,
            Appointment.date.between(first_str, last_str),
        )
        .all()
    )

    appointments_this_month = len(month_appts)
    completed_month = sum(1 for a in month_appts if (a.status or "").upper() == "COMPLETED")
    cancelled_month = sum(1 for a in month_appts if (a.status or "").upper() == "CANCELLED")

    this_month_status_counts = {"completed": 0, "booked": 0, "cancelled": 0}
    for a in month_appts:
        s = (a.status or "").upper()
        if s == "COMPLETED":
            this_month_status_counts["completed"] += 1
        elif s == "BOOKED":
            this_month_status_counts["booked"] += 1
        elif s == "CANCELLED":
            this_month_status_counts["cancelled"] += 1

    all_appts = Appointment.query.filter(Appointment.doctor_id == user_id).all()
    status_counts = {"completed": 0, "booked": 0, "cancelled": 0}
    for a in all_appts:
        s = (a.status or "").upper()
        if s == "COMPLETED":
            status_counts["completed"] += 1
        elif s == "BOOKED":
            status_counts["booked"] += 1
        elif s == "CANCELLED":
            status_counts["cancelled"] += 1

    monthly_trend = [0] * 12
    for a in all_appts:
        if not a.date:
            continue
        try:
            d_obj = datetime.strptime(a.date, "%Y-%m-%d").date()
        except ValueError:
            if isinstance(a.date, date):
                d_obj = a.date
            else:
                continue
        if d_obj.year != today.year:
            continue
        monthly_trend[d_obj.month - 1] += 1

    return {
        "total_patients": total_patients,
        "appointments_this_month": appointments_this_month,
        "completed": completed_month,
        "cancelled": cancelled_month,
        "monthly_trend": monthly_trend,
        "status_counts": status_counts,
        "this_month_status_counts": this_month_status_counts,
    }


@jwt_required()
@cached(prefix="doctor_stats", ttl=60)
def doctor_stats():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status
    return _doctor_stats_impl()


@jwt_required()
def doctor_monthly_report():
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    user = User.query.get(user_id)
    doctor = Doctor.query.get(user_id)

    if doctor and doctor.full_name:
        doctor_name = doctor.full_name
    elif user:
        doctor_name = user.username
    else:
        doctor_name = f"Doctor #{user_id}"

    month_param = request.args.get("month")
    today = _today()

    try:
        if month_param:
            year_str, month_str = month_param.split("-")
            year = int(year_str)
            month = int(month_str)
        else:
            year = today.year
            month = today.month
    except Exception:
        return jsonify({"message": "Invalid month format, expected YYYY-MM"}), 400

    last_day_num = monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day_num)

    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    appts = (
        Appointment.query
        .filter(
            Appointment.doctor_id == user_id,
            Appointment.date.between(start_str, end_str),
        )
        .order_by(Appointment.date.asc(), Appointment.time.asc())
        .all()
    )

    patient_ids = {a.patient_id for a in appts if a.patient_id}
    patients = {}
    if patient_ids:
        patients = {
            p.id: p
            for p in Patient.query.filter(Patient.id.in_(patient_ids)).all()
        }

    appt_ids = [a.id for a in appts]
    treatments = {}
    if appt_ids:
        t_rows = Treatment.query.filter(
            Treatment.appointment_id.in_(appt_ids)
        ).all()
        treatments = {t.appointment_id: t for t in t_rows}

    total_appts = len(appts)
    completed = cancelled = booked = 0
    for a in appts:
        s = (a.status or "").upper()
        if s == "COMPLETED":
            completed += 1
        elif s == "CANCELLED":
            cancelled += 1
        elif s == "BOOKED":
            booked += 1

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=50,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    title_style = ParagraphStyle(
        "TitleBig",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        spaceAfter=6,
    )

    small_gray = ParagraphStyle(
        "SmallGray",
        parent=normal,
        fontSize=9,
        textColor=colors.grey,
        leading=11,
    )

    elements = []

    title_text = "Monthly Appointment Report"
    month_label = f"{year}-{month:02d}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(
        Paragraph(f"Doctor: <b>{doctor_name}</b>", normal)
    )
    elements.append(Paragraph(f"Month: <b>{month_label}</b>", normal))
    elements.append(
        Paragraph(
            f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            small_gray,
        )
    )
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Summary", subtitle_style))

    summary_data = [
        ["Metric", "Value"],
        ["Total appointments", str(total_appts)],
        ["Completed", str(completed)],
        ["Booked", str(booked)],
        ["Cancelled", str(cancelled)],
    ]

    summary_table = Table(summary_data, colWidths=[200, 80])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9ecef")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, 0), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )

    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Appointments Detail", subtitle_style))

    if not appts:
        elements.append(
            Paragraph(
                "No appointments found for this month.",
                normal,
            )
        )
    else:
        table_data = [
            [
                Paragraph("<b>#</b>", normal),
                Paragraph("<b>Date</b>", normal),
                Paragraph("<b>Time</b>", normal),
                Paragraph("<b>Patient</b>", normal),
                Paragraph("<b>Status</b>", normal),
                Paragraph("<b>Reason / Diagnosis</b>", normal),
                Paragraph("<b>Follow-up</b>", normal),
            ]
        ]

        for idx, a in enumerate(appts, start=1):
            p = patients.get(a.patient_id)
            t = treatments.get(a.id)

            patient_name = (
                p.full_name if p else (f"Patient #{a.patient_id}" if a.patient_id else "")
            )
            status = a.status or ""
            reason = (a.reason or "").strip()
            diagnosis = (getattr(t, "diagnosis", "") or "").strip()
            follow_up = (getattr(t, "follow_up_date", "") or "").strip()

            detail_parts = []
            if reason:
                detail_parts.append(f"Reason: {reason}")
            if diagnosis:
                detail_parts.append(f"Diagnosis: {diagnosis}")
            detail_text = "<br/>".join(detail_parts) if detail_parts else ""

            row = [
                Paragraph(str(idx), normal),
                Paragraph(a.date or "", normal),
                Paragraph(a.time or "", normal),
                Paragraph(patient_name or "", normal),
                Paragraph(status, normal),
                Paragraph(detail_text, small_gray if detail_text else normal),
                Paragraph(follow_up or "", normal),
            ]
            table_data.append(row)

        col_widths = [30, 70, 55, 150, 70, 260, 70]

        appt_table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1,
        )
        appt_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dee2e6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("ALIGN", (1, 0), (2, 0), "CENTER"),
                    ("ALIGN", (4, 0), (4, 0), "CENTER"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 1), (0, -1), "CENTER"),
                    ("ALIGN", (1, 1), (2, -1), "CENTER"),
                    ("ALIGN", (4, 1), (4, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [colors.whitesmoke, colors.white]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        elements.append(appt_table)

    doc.build(elements)

    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    filename = f"doctor_report_{year}-{month:02d}.pdf"
    headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(pdf_bytes, headers=headers)
