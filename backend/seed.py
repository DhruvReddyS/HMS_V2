# seed.py
"""
Seed script for HMS:
- DROP all existing tables and CREATE fresh ones
- 1 Admin user
- 5 Doctors (with profiles)
- 10 Patients (with profiles)
- Rich, realistic appointments across:
    * previous month  → mostly COMPLETED / some CANCELLED
    * this month      → past days COMPLETED/CANCELLED, future days mostly BOOKED
    * next month      → mostly BOOKED / some CANCELLED
- Detailed Treatment records for ALL COMPLETED appointments
- Doctor availability for next 30 days
"""

from datetime import date, datetime, timedelta
import random

from flask import Flask

from config import Config
from models import (
    db,
    User,
    Patient,
    Doctor,
    Appointment,
    Treatment,
    DoctorAvailability,
)

# Same slot grid as in your app
DEFAULT_TIME_SLOTS = [
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    # 13:00–14:00 is lunch break → no slots
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def reset_db():
    print("➡ Resetting database (drop_all + create_all)...")
    db.drop_all()
    db.create_all()
    print("✔ Database reset complete.")


def add_admin():
    print("➡ Creating admin user...")
    admin = User(
        username="admin",
        email="admin@hms.local",
        role="admin",
        is_active=True,
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    print(f"✔ Admin created: {admin}")
    return admin


def seed_doctors():
    print("➡ Creating doctors...")

    # NOTE: full_name has NO "Dr." prefix as requested
    doctor_specs = [
        {
            "username": "doctor1",
            "email": "doctor1@hms.local",
            "full_name": "Arya Srinivasan",
            "specialization": "Cardiology",
            "experience_years": 12,
            "about": (
                "Senior interventional cardiologist with a focus on preventive cardiology, "
                "lifestyle modification counselling and post-angioplasty care."
            ),
        },
        {
            "username": "doctor2",
            "email": "doctor2@hms.local",
            "full_name": "Rahul Menon",
            "specialization": "Orthopedics",
            "experience_years": 9,
            "about": (
                "Orthopedic surgeon specializing in sports injuries, ACL reconstruction, "
                "and long-term rehabilitation of knee and shoulder conditions."
            ),
        },
        {
            "username": "doctor3",
            "email": "doctor3@hms.local",
            "full_name": "Sara Kulkarni",
            "specialization": "Neurology",
            "experience_years": 10,
            "about": (
                "Consultant neurologist with interest in chronic migraine, epilepsy management, "
                "and stroke prevention clinics."
            ),
        },
        {
            "username": "doctor4",
            "email": "doctor4@hms.local",
            "full_name": "Vikram Reddy",
            "specialization": "Pediatrics",
            "experience_years": 8,
            "about": (
                "Pediatrician providing growth monitoring, vaccination counselling, and management "
                "of common childhood infections and allergies."
            ),
        },
        {
            "username": "doctor5",
            "email": "doctor5@hms.local",
            "full_name": "Nisha Kapoor",
            "specialization": "Dermatology",
            "experience_years": 7,
            "about": (
                "Dermatologist specialising in acne, pigmentary disorders, hairfall evaluation "
                "and evidence-based skincare routines."
            ),
        },
    ]

    doctors = []

    for spec in doctor_specs:
        user = User(
            username=spec["username"],
            email=spec["email"],
            role="doctor",
            is_active=True,
        )
        user.set_password("doctor123")  # as requested

        doctor = Doctor(
            user=user,
            full_name=spec["full_name"],
            specialization=spec["specialization"],
            experience_years=spec["experience_years"],
            about=spec["about"],
        )

        db.session.add(user)
        db.session.add(doctor)
        doctors.append(doctor)

    db.session.commit()
    print(f"✔ Created {len(doctors)} doctors.")
    return doctors


def seed_patients():
    print("➡ Creating patients...")

    # usernames patient1..patient10, full_name kept realistic
    patient_specs = [
        {
            "username": "patient1",
            "email": "patient1@hms.local",
            "full_name": "Ravi Kumar",
            "gender": "Male",
            "dob": "1990-05-14",
            "address": "Flat 302, Green Meadows Apartments, Hyderabad",
            "phone": "9876500010",
            "height_cm": 172.0,
            "weight_kg": 78.5,
            "blood_group": "B+",
            "is_disabled": False,
        },
        {
            "username": "patient2",
            "email": "patient2@hms.local",
            "full_name": "Anjali Sharma",
            "gender": "Female",
            "dob": "1994-09-22",
            "address": "Villa 12, Sunrise Enclave, Bengaluru",
            "phone": "9876500011",
            "height_cm": 160.0,
            "weight_kg": 62.0,
            "blood_group": "O+",
            "is_disabled": False,
        },
        {
            "username": "patient3",
            "email": "patient3@hms.local",
            "full_name": "Mahesh Reddy",
            "gender": "Male",
            "dob": "1985-01-08",
            "address": "H.No 4-2/11, KPHB, Hyderabad",
            "phone": "9876500012",
            "height_cm": 175.0,
            "weight_kg": 90.0,
            "blood_group": "A+",
            "is_disabled": False,
        },
        {
            "username": "patient4",
            "email": "patient4@hms.local",
            "full_name": "Sneha Patil",
            "gender": "Female",
            "dob": "1998-12-02",
            "address": "Flat 502, Lake View Towers, Pune",
            "phone": "9876500013",
            "height_cm": 158.0,
            "weight_kg": 54.0,
            "blood_group": "AB+",
            "is_disabled": False,
        },
        {
            "username": "patient5",
            "email": "patient5@hms.local",
            "full_name": "Arjun Tiwari",
            "gender": "Male",
            "dob": "2000-07-19",
            "address": "Hostel Block B, MVSR Campus",
            "phone": "9876500014",
            "height_cm": 181.0,
            "weight_kg": 72.0,
            "blood_group": "O-",
            "is_disabled": False,
        },
        {
            "username": "patient6",
            "email": "patient6@hms.local",
            "full_name": "Meera Joshi",
            "gender": "Female",
            "dob": "1989-03-30",
            "address": "Row House 7, Serene County, Mumbai",
            "phone": "9876500015",
            "height_cm": 165.0,
            "weight_kg": 70.5,
            "blood_group": "B-",
            "is_disabled": False,
        },
        {
            "username": "patient7",
            "email": "patient7@hms.local",
            "full_name": "Kiran Verma",
            "gender": "Male",
            "dob": "1978-11-11",
            "address": "Independent House, Indiranagar, Bengaluru",
            "phone": "9876500016",
            "height_cm": 170.0,
            "weight_kg": 82.0,
            "blood_group": "A-",
            "is_disabled": False,
        },
        {
            "username": "patient8",
            "email": "patient8@hms.local",
            "full_name": "Lata Mishra",
            "gender": "Female",
            "dob": "1975-04-05",
            "address": "Ground Floor, Old City, Hyderabad",
            "phone": "9876500017",
            "height_cm": 155.0,
            "weight_kg": 68.0,
            "blood_group": "B+",
            "is_disabled": True,
        },
        {
            "username": "patient9",
            "email": "patient9@hms.local",
            "full_name": "Naveen Chowdary",
            "gender": "Male",
            "dob": "1992-02-18",
            "address": "Flat 101, Tech Park Residency, Hyderabad",
            "phone": "9876500018",
            "height_cm": 177.0,
            "weight_kg": 76.0,
            "blood_group": "O+",
            "is_disabled": False,
        },
        {
            "username": "patient10",
            "email": "patient10@hms.local",
            "full_name": "Pavani Devi",
            "gender": "Female",
            "dob": "2001-08-09",
            "address": "Girls Hostel, MVSR Engineering College",
            "phone": "9876500019",
            "height_cm": 162.0,
            "weight_kg": 58.0,
            "blood_group": "AB-",
            "is_disabled": False,
        },
    ]

    patients = []

    for spec in patient_specs:
        user = User(
            username=spec["username"],
            email=spec["email"],
            role="patient",
            is_active=True,
        )
        user.set_password("patient123")  # as requested

        patient = Patient(
            user=user,
            full_name=spec["full_name"],
            gender=spec["gender"],
            dob=spec["dob"],
            address=spec["address"],
            phone=spec["phone"],
            height_cm=spec["height_cm"],
            weight_kg=spec["weight_kg"],
            blood_group=spec["blood_group"],
            is_disabled=spec["is_disabled"],
            profile_photo_url=None,
        )

        db.session.add(user)
        db.session.add(patient)
        patients.append(patient)

    db.session.commit()
    print(f"✔ Created {len(patients)} patients.")
    return patients


def _date_to_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def create_detailed_treatment(appointment: Appointment, scenario: str):
    """
    Attach a rich Treatment record to a completed appointment.
    Different 'scenario' strings generate different realistic content.
    """
    if scenario == "chest_pain":
        t = Treatment(
            appointment=appointment,
            diagnosis="Stable angina with underlying dyslipidemia and sedentary lifestyle.",
            prescription=(
                "Tab. Ecosprin AV 75/20 mg | 1-0-0 | After dinner | 90 days\n"
                "Tab. Metoprolol 25 mg | 0-0-1 | Night | 30 days\n"
                "S.L. Sorbitrate 5 mg | SOS | Max 3 tablets per day\n"
                "Tab. Vitamin D3 60k | 1 tab weekly | 6 weeks"
            ),
            notes=(
                "Explained difference between cardiac and muscular chest pain. "
                "Reviewed previous ECG and current vitals – stable. "
                "Patient counselled on avoiding sudden exertion; asked to maintain a symptom diary. "
                "Emergency red flags explained: chest pain at rest, severe sweating, radiation to jaw/left arm."
            ),
            visit_type="IN_PERSON",
            tests_text=(
                "ECG (resting), 2D Echo, Fasting lipid profile, Fasting blood sugar, TMT (after cardiology clearance)"
            ),
            precautions=(
                "Avoid heavy meals late at night, restrict oily and fried foods, "
                "30 minutes brisk walking on 5 days per week after 2 weeks if symptom-free, "
                "stop smoking completely, limit tea/coffee to 2 cups/day."
            ),
            follow_up_date=_date_to_str(date.today() + timedelta(days=21)),
        )
    elif scenario == "migraine":
        t = Treatment(
            appointment=appointment,
            diagnosis="Chronic migraine without aura, likely triggered by irregular sleep and screen exposure.",
            prescription=(
                "Tab. Propranolol 20 mg | 1-0-1 | After food | 30 days\n"
                "Tab. Naproxen 500 mg | SOS for severe headache | Max 2/day\n"
                "Tab. Vitamin B2 (Riboflavin) 100 mg | 1-0-0 | 60 days"
            ),
            notes=(
                "Explained migraine nature, common triggers and importance of lifestyle modification. "
                "Asked patient to maintain a headache diary (intensity, duration, triggers, response to meds). "
                "Discussed stress management techniques and sleep hygiene."
            ),
            visit_type="ONLINE",
            tests_text=(
                "MRI brain (plain), Serum Vitamin D3, CBC, Thyroid profile (TSH, Free T4)"
            ),
            precautions=(
                "Maintain fixed sleep and wake-up times, avoid skipping meals, "
                "limit continuous screen time to max 30–40 minutes at a stretch, "
                "stay hydrated (2.5–3 L water/day), avoid loud music and bright flashing lights."
            ),
            follow_up_date=_date_to_str(date.today() + timedelta(days=30)),
        )
    elif scenario == "pediatric_fever":
        t = Treatment(
            appointment=appointment,
            diagnosis="Acute viral upper respiratory infection with low-grade fever.",
            prescription=(
                "Syp. Paracetamol 250 mg/5ml | 10 ml SOS | Every 6 hours for fever > 100°F\n"
                "Syp. Cetirizine 5 mg/5ml | 5 ml at night | 5 days\n"
                "Saline nasal drops | 2 drops each nostril | 4–5 times/day"
            ),
            notes=(
                "Child active and playful, hydration status good. No signs of serious bacterial infection. "
                "Explained fever as a natural defence mechanism. Parents advised not to overuse antibiotics."
            ),
            visit_type="IN_PERSON",
            tests_text="None immediately required; consider CBC and CRP if fever persists beyond 5 days.",
            precautions=(
                "Ensure adequate oral fluids (ORS, soups, coconut water), "
                "light, easily digestible home food, avoid forced feeding. "
                "Monitor temperature every 4–6 hours and watch for breathing difficulty or poor feeding."
            ),
            follow_up_date=_date_to_str(date.today() + timedelta(days=3)),
        )
    elif scenario == "knee_pain":
        t = Treatment(
            appointment=appointment,
            diagnosis="Early osteoarthritis of knee with quadriceps muscle weakness.",
            prescription=(
                "Tab. Aceclofenac 100 mg + Paracetamol 325 mg | 1-0-1 | After food | 5 days\n"
                "Tab. Calcium + Vitamin D3 | 1-0-0 | 3 months\n"
                "Topical Diclofenac gel | Apply thin layer | 2–3 times/day on knee joint"
            ),
            notes=(
                "Explained degenerative nature of osteoarthritis and importance of weight reduction. "
                "Demonstrated quadriceps strengthening and hamstring stretching exercises in detail. "
                "Discussed role of physiotherapy and footwear modification."
            ),
            visit_type="IN_PERSON",
            tests_text="X-ray both knees (standing), Serum Vitamin D3, Serum Calcium.",
            precautions=(
                "Avoid squatting, sitting cross-legged, climbing stairs repeatedly. "
                "Use Western toilet, use handrails while using stairs. "
                "Target weight loss of 4–5 kg over next 3 months."
            ),
            follow_up_date=_date_to_str(date.today() + timedelta(days=28)),
        )
    elif scenario == "acne":
        t = Treatment(
            appointment=appointment,
            diagnosis="Moderate inflammatory acne vulgaris with early post-inflammatory hyperpigmentation.",
            prescription=(
                "Clindamycin + Nicotinamide gel | Apply thin layer over active acne | Morning | 8 weeks\n"
                "Adapalene 0.1% gel | Pea-sized amount over entire face | Night | 8–12 weeks\n"
                "Non-comedogenic moisturizer | Twice daily as needed\n"
                "Gel-based sunscreen SPF 30+ | Apply every 3–4 hours during day"
            ),
            notes=(
                "Explained that acne treatment requires 8–12 weeks for visible improvement. "
                "Advised patient not to squeeze/pick lesions to avoid scarring. "
                "Discussed skincare routine suitable for oily, acne-prone skin."
            ),
            visit_type="IN_PERSON",
            tests_text="No routine tests required at this stage; consider hormonal workup if resistant.",
            precautions=(
                "Avoid heavy, oily cosmetics and home remedies like lemon or toothpaste on skin. "
                "Use gentle cleanser twice a day, avoid over-washing. "
                "Maintain regular sleep, reduce high-glycemic foods and sugary drinks."
            ),
            follow_up_date=_date_to_str(date.today() + timedelta(days=42)),
        )
    else:
        # generic fallback
        t = Treatment(
            appointment=appointment,
            diagnosis="General medical consultation.",
            prescription="Tab. Multivitamin | 1-0-0 | 30 days",
            notes="Generic follow-up advice.",
            visit_type="IN_PERSON",
            tests_text="CBC, Basic metabolic panel",
            precautions="Maintain hydration and balanced diet.",
            follow_up_date=_date_to_str(date.today() + timedelta(days=30)),
        )

    db.session.add(t)
    return t


def _daterange(start: date, end: date):
    """Inclusive date range [start, end]."""
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def _reason_for_scenario(scenario: str, phase: str) -> str:
    """
    phase: 'initial', 'followup', 'future'
    """
    if scenario == "chest_pain":
        if phase == "initial":
            return "Intermittent chest discomfort on exertion for 3 weeks."
        elif phase == "followup":
            return "Review visit for chest pain, medication adjustment and lifestyle counselling."
        else:
            return "Scheduled cardiac follow-up and review of blood test reports."
    if scenario == "migraine":
        if phase == "initial":
            return "Recurrent right-sided headache with nausea and photophobia for several months."
        elif phase == "followup":
            return "Follow-up for migraine control and review of headache diary."
        else:
            return "Planned neurology review after trial of preventive migraine therapy."
    if scenario == "pediatric_fever":
        if phase == "initial":
            return "Fever with cold and mild cough for 2 days in child."
        elif phase == "followup":
            return "Follow-up for recent viral fever, appetite and activity check."
        else:
            return "Scheduled pediatric review for growth monitoring and vaccination counselling."
    if scenario == "knee_pain":
        if phase == "initial":
            return "Knee pain while climbing stairs and after prolonged walking."
        elif phase == "followup":
            return "Follow-up for knee osteoarthritis and exercise compliance."
        else:
            return "Planned review for knee osteoarthritis and physiotherapy response."
    if scenario == "acne":
        if phase == "initial":
            return "Persistent acne over cheeks and forehead, worsening before periods."
        elif phase == "followup":
            return "Review of acne response to topical regimen and sunscreen use."
        else:
            return "Dermatology review for acne scarring and pigmentation management."
    # fallback
    return "General medical consultation."


def seed_appointments_and_treatments(doctors, patients):
    """
    DAILY appointments for every doctor across:
    - Previous month      → mostly COMPLETED (with treatments) / some CANCELLED
    - This month (past)   → COMPLETED/CANCELLED
    - This month (future) → mostly BOOKED
    - Next month          → mostly BOOKED / some CANCELLED

    Each doctor has multiple slots per day, with realistic reasons and rich treatments.
    """
    print("➡ Creating appointments + treatments across full months (daily)...")

    today = date.today()

    # ----- Month boundaries -----
    first_this_month = today.replace(day=1)
    # prev month
    last_prev_month = first_this_month - timedelta(days=1)
    first_prev_month = last_prev_month.replace(day=1)
    # next month
    first_next_month = (first_this_month + timedelta(days=32)).replace(day=1)
    last_this_month = first_next_month - timedelta(days=1)
    first_month_after_next = (first_next_month + timedelta(days=32)).replace(day=1)
    last_next_month = first_month_after_next - timedelta(days=1)

    prev_month_days = list(_daterange(first_prev_month, last_prev_month))
    this_month_days = list(_daterange(first_this_month, last_this_month))
    next_month_days = list(_daterange(first_next_month, last_next_month))

    scenarios = ["chest_pain", "migraine", "pediatric_fever", "knee_pain", "acne"]

    # Map each doctor to a scenario type
    doctor_scenario_map = {}
    for i, doctor in enumerate(doctors):
        doctor_scenario_map[doctor.id] = scenarios[i % len(scenarios)]

    all_appointments = []

    # Track used slots to avoid double-booking per doctor/date
    used_slots = {}  # key: (doctor_id, date_str) -> set of time slots

    def get_free_slots(doctor_id, date_str, count: int):
        key = (doctor_id, date_str)
        if key not in used_slots:
            used_slots[key] = set()
        free = []
        for slot in DEFAULT_TIME_SLOTS:
            if slot not in used_slots[key]:
                used_slots[key].add(slot)
                free.append(slot)
                if len(free) >= count:
                    break
        return free

    # rotate through patients for variety
    patient_cycle = patients * 5  # just to be safe
    patient_index = 0

    def next_patient():
        nonlocal patient_index
        p = patient_cycle[patient_index % len(patient_cycle)]
        patient_index += 1
        return p

    def pick_status_for_day(day: date, month_type: str):
        """
        month_type: 'prev' | 'this_past' | 'this_future' | 'next'
        Returns one of 'COMPLETED', 'CANCELLED', 'BOOKED'
        """
        if month_type == "prev":
            # previous month: mostly COMPLETED
            return random.choices(
                ["COMPLETED", "CANCELLED"],
                weights=[0.8, 0.2],
                k=1,
            )[0]
        if month_type == "this_past":
            # earlier this month: mix of COMPLETED/CANCELLED
            return random.choices(
                ["COMPLETED", "CANCELLED"],
                weights=[0.75, 0.25],
                k=1,
            )[0]
        if month_type == "this_future":
            # remaining days this month: mostly BOOKED
            return random.choices(
                ["BOOKED", "CANCELLED"],
                weights=[0.8, 0.2],
                k=1,
            )[0]
        if month_type == "next":
            # next month: mostly BOOKED, some CANCELLED (planned but patient might cancel)
            return random.choices(
                ["BOOKED", "CANCELLED"],
                weights=[0.85, 0.15],
                k=1,
            )[0]
        return "BOOKED"

    # For each doctor, create daily appointments across all months
    for doctor in doctors:
        scenario = doctor_scenario_map[doctor.id]

        # -------- Previous month (daily) --------
        for day in prev_month_days:
            d_str = _date_to_str(day)
            # 2–3 appointments per doctor per day
            slots = get_free_slots(doctor.id, d_str, random.choice([2, 3]))
            for slot in slots:
                patient = next_patient()
                status = pick_status_for_day(day, "prev")
                reason_phase = "initial" if day <= prev_month_days[len(prev_month_days) // 2] else "followup"

                appt = Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    date=d_str,
                    time=slot,
                    status=status,
                    reason=_reason_for_scenario(scenario, reason_phase),
                )
                db.session.add(appt)
                all_appointments.append(appt)

                if status == "COMPLETED":
                    create_detailed_treatment(appt, scenario)

        # -------- This month (daily) --------
        for day in this_month_days:
            d_str = _date_to_str(day)
            slots = get_free_slots(doctor.id, d_str, random.choice([2, 3, 4]))
            for slot in slots:
                patient = next_patient()
                if day < today:
                    month_type = "this_past"
                    phase = "followup"
                else:
                    month_type = "this_future"
                    phase = "future"

                status = pick_status_for_day(day, month_type)
                appt = Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    date=d_str,
                    time=slot,
                    status=status,
                    reason=_reason_for_scenario(scenario, phase),
                )
                db.session.add(appt)
                all_appointments.append(appt)

                if status == "COMPLETED":
                    create_detailed_treatment(appt, scenario)

        # -------- Next month (daily) --------
        for day in next_month_days:
            d_str = _date_to_str(day)
            # 2–3 appointments per day
            slots = get_free_slots(doctor.id, d_str, random.choice([2, 3]))
            for slot in slots:
                patient = next_patient()
                status = pick_status_for_day(day, "next")
                appt = Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    date=d_str,
                    time=slot,
                    status=status,
                    reason=_reason_for_scenario(scenario, "future"),
                )
                db.session.add(appt)
                all_appointments.append(appt)

                if status == "COMPLETED":
                    create_detailed_treatment(appt, scenario)

    db.session.commit()
    print(f"✔ Created {len(all_appointments)} appointments with detailed treatments for COMPLETED ones.")


def seed_doctor_availability(doctors, days_ahead: int = 30):
    """
    Create doctor availability for the next `days_ahead` days for each doctor.
    This supports daily booking + reminder flows.
    """
    print(f"➡ Creating sample doctor availability for next {days_ahead} days...")

    start = date.today()
    days = [start + timedelta(days=i) for i in range(0, days_ahead)]

    for d in doctors:
        for day in days:
            for slot in DEFAULT_TIME_SLOTS:
                # randomly mark some slots unavailable
                is_available = random.choice([True, True, True, False])
                avail = DoctorAvailability(
                    doctor_id=d.id,
                    date=_date_to_str(day),
                    time_slot=slot,
                    is_available=is_available,
                )
                db.session.add(avail)

    db.session.commit()
    print("✔ Doctor availability seeded.")


def main():
    app = create_app()
    with app.app_context():
        print("➡ Seeding demo HMS data (admin, doctors, patients, appointments, treatments)...")
        reset_db()
        add_admin()
        doctors = seed_doctors()
        patients = seed_patients()
        seed_appointments_and_treatments(doctors, patients)
        seed_doctor_availability(doctors, days_ahead=30)
        print("🎉 Seeding complete.")


if __name__ == "__main__":
    main()
