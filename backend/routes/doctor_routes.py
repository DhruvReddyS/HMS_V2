# routes/doctor_routes.py

from datetime import datetime, date, timedelta

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import or_

from cache_utils import cached, cache_delete_pattern  # ✅ caching helpers

from models import (
    db,
    User,
    Doctor,
    Patient,
    Appointment,
    Treatment,
    DoctorAvailability,
)

# -----------------------------
# Helpers & shared constants
# -----------------------------
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
    """
    Check JWT 'role' == 'doctor'.
    Returns (ok, resp, status). If not ok, return resp,status from view.
    """
    claims = get_jwt()
    role = claims.get("role")
    if role != "doctor":
        return False, jsonify({"message": "Doctor access required"}), 403
    return True, None, None


def _get_doctor_id() -> int:
    """Convenience helper to get current doctor's user id as int."""
    return int(get_jwt_identity())


# Global slot grid used by doctor availability (and by patient-side logic)
# 1–2 PM lunch break is simply not in this list
DEFAULT_TIME_SLOTS = [
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    # 13:00–14:00 → lunch break
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
]


# =============================
# 1. Dashboard summary
# GET /api/doctor/dashboard-summary
# =============================
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

    # Week range (for stats) – ISO strings
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    week_start_str = week_start.isoformat()
    week_end_str = week_end.isoformat()

    # Today's appointments
    todays_appts = (
        Appointment.query
        .filter(
            Appointment.doctor_id == user_id,
            Appointment.date == today_str,
        )
        .order_by(Appointment.time.asc())
        .all()
    )

    # Stats for today
    today_total = len(todays_appts)
    today_booked = sum(1 for a in todays_appts if (a.status or "").upper() == "BOOKED")
    today_completed = sum(1 for a in todays_appts if (a.status or "").upper() == "COMPLETED")
    pending_visits = today_booked

    # Weekly completed visits
    week_completed = (
        Appointment.query
        .filter(
            Appointment.doctor_id == user_id,
            Appointment.date.between(week_start_str, week_end_str),
            Appointment.status == "COMPLETED",
        )
        .count()
    )

    # Recent / assigned patients (last 50 appts)
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

    # Collect patient ids from:
    #  - recent appts (for "assigned patients" section)
    #  - today's appts (for "upcoming appointments" names)
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

    # --- has_treatment for today's appointments ---
    todays_ids = [a.id for a in todays_appts]
    treated_ids = set()
    if todays_ids:
        treat_rows = Treatment.query.filter(
            Treatment.appointment_id.in_(todays_ids)
        ).all()
        treated_ids = {t.appointment_id for t in treat_rows}

    # Build today's upcoming appointments payload
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

    # Return dict so @cached can store + jsonify
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


# =============================
# 2. List / filter appointments
# GET /api/doctor/appointments
# =============================
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

    # Return dict so @cached can store + jsonify
    return {"appointments": [_to_dict(a) for a in appts]}


# =============================
# 3. Update appointment status
# POST /api/doctor/appointments/<int:appointment_id>/status
# =============================
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

    # 🔥 Invalidate caches impacted by this change
    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:doctor_patient_history:*")
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_appointments:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({"message": "Status updated successfully.", "status": new_status})


# =============================
# 4. Save treatment
# POST /api/doctor/appointments/<int:appointment_id>/treatment
# =============================
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

    # 🔥 Invalidate caches: treatment affects stats, history, flags
    cache_delete_pattern("API:doctor_dashboard:*")
    cache_delete_pattern("API:doctor_appointments:*")
    cache_delete_pattern("API:doctor_patient_history:*")
    cache_delete_pattern("API:doctor_treatment:*")
    cache_delete_pattern("API:patient_appointments:*")
    cache_delete_pattern("API:patient_history:*")
    cache_delete_pattern("API:admin_stats:*")
    cache_delete_pattern("API:admin_appointments:*")

    return jsonify({"message": "Treatment details saved successfully."})


# =============================
# 4b. Get treatment
# GET /api/doctor/appointments/<int:appointment_id>/treatment
# =============================
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
        return {"exists": False, "treatment": None}, 200

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

    return {"exists": True, "treatment": treatment_payload}, 200


# =============================
# 5. Patient history (for THIS doctor)
# GET /api/doctor/patient-history
# =============================
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

    # Return dict for caching
    return {"patient": patient_payload, "visits": visits}


# =============================
# 6. Availability – grid + bulk + toggle
# =============================

@jwt_required()
@cached(prefix="doctor_availability", ttl=60)
def doctor_availability():
    """
    GET /api/doctor/availability?start_date=YYYY-MM-DD
    → return 7-day availability grid with bookings info.
    """
    ok, resp, status = _require_doctor_role()
    if not ok:
        return resp, status

    user_id = _get_doctor_id()
    start_date = _parse_date_param("start_date", default_today=True)
    end_date = start_date + timedelta(days=6)

    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    # 1) Doctor availability overrides
    av_rows = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == user_id,
        DoctorAvailability.date.between(start_str, end_str),
    ).all()
    av_map = {(row.date, row.time_slot): row.is_available for row in av_rows}

    # 2) Appointments (BOOKED/COMPLETED block the slot)
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
            is_available = av_map.get((d_str, ts), True)  # default: available
            booking_status = appt_map.get((d_str, ts))     # BOOKED / COMPLETED / None

            slots.append({
                "time_slot": ts,
                "is_available": is_available,
                "booking_status": booking_status,
            })

        days.append({"date": d_str, "slots": slots})

    # Return dict (cached)
    return {"days": days}


@jwt_required()
def doctor_update_availability():
    """
    POST /api/doctor/availability/bulk

    Body:
    {
      "date": "2025-11-28",
      "slots": [
        {"time_slot": "09:00", "is_available": true},
        {"time_slot": "09:30", "is_available": false}
      ]
    }
    """
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

    # 🔥 Invalidate availability + patient slot caches
    cache_delete_pattern("API:doctor_availability:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({"message": "Availability updated successfully"})


@jwt_required()
def doctor_toggle_availability():
    """
    POST /api/doctor/availability/toggle

    Body:
    {
      "date": "2025-11-28",
      "time_slot": "09:00",
      // optional:
      // "is_available": false   ← if not sent, backend will toggle
    }
    """
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
        # default: if not exists, create row; if is_available provided, use it;
        # else treat toggle as "make it unavailable"
        new_val = False if body_is_av is None else bool(body_is_av)
        slot = DoctorAvailability(
            doctor_id=user_id,
            date=date_str,
            time_slot=time_slot,
            is_available=new_val,
        )
        db.session.add(slot)

    db.session.commit()

    # 🔥 Invalidate availability + patient slot caches
    cache_delete_pattern("API:doctor_availability:*")
    cache_delete_pattern("API:patient_slots:*")

    return jsonify({
        "message": "Slot updated",
        "date": date_str,
        "time_slot": time_slot,
        "is_available": new_val,
    }), 200
