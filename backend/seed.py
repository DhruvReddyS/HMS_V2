# seed.py

import random
from datetime import datetime, date, time as dtime, timedelta

from faker import Faker

from app import create_app
from models import db, User, Patient, Doctor, Appointment, Treatment

fake = Faker("en_IN")

# ----------------------------
# Reference data
# ----------------------------

SPECIALIZATIONS = [
    "Cardiology",
    "Orthopedics",
    "Neurology",
    "Pediatrics",
    "General Medicine",
    "Dermatology",
    "ENT",
    "Gastroenterology",
    "Pulmonology",
    "Psychiatry",
]

DIAGNOSES = [
    "Upper respiratory tract infection",
    "Type 2 Diabetes Mellitus",
    "Hypertension",
    "Acute gastritis",
    "Migraine",
    "Allergic rhinitis",
    "Low back pain",
    "Viral fever",
    "Anxiety disorder",
    "Iron deficiency anemia",
]

MEDICINE_PATTERNS = [
    "DOLO650-1-1-1 | AZITH500-1-0-0",
    "METFORMIN500-0-1-1 | GLIMIPRIDE1-0-0-1",
    "PANTOP40-1-0-1 | DIGENE-0-0-1",
    "AMLO5-1-0-0 | ATOR20-0-0-1",
    "LEVOCET5-0-0-1",
]

TESTS_LIST = [
    "CBC",
    "Blood Sugar (F/PP)",
    "Lipid Profile",
    "LFT",
    "KFT",
    "X-Ray Chest",
    "ECG",
    "Vitamin D",
    "Thyroid Profile",
]

PRECAUTIONS_LIST = [
    "Drink plenty of water, avoid outside food.",
    "Low salt, low oil diet and regular exercise.",
    "Take adequate rest and avoid screen time at night.",
    "Avoid cold drinks and very cold environments.",
    "Do not skip medications; follow up if symptoms worsen.",
]

VISIT_TYPES = ["IN_PERSON", "ONLINE"]


# ----------------------------
# Helper functions
# ----------------------------

def wipe_non_admin_data():
    """
    Dev-only helper: wipe everything except admin users.
    """
    print("➡ Wiping existing non-admin data (dev only)...")

    # Delete child tables first due to FK constraints
    Treatment.query.delete()
    Appointment.query.delete()
    Patient.query.delete()
    Doctor.query.delete()

    # Delete non-admin users
    User.query.filter(User.role != "admin").delete()

    db.session.commit()
    print("✔ Wipe complete.")


def ensure_admin():
    """
    Ensure there is at least one admin user.
    """
    admin = User.query.filter_by(role="admin").first()
    if admin:
        print(f"✔ Admin already exists: {admin.username}")
        return admin

    admin = User(
        username="admin",
        email="admin@hms.com",
        role="admin",
        is_active=True,
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    print("✔ Created default admin user: admin / admin123")
    return admin


def seed_doctors(count: int = 15):
    """
    Seed doctors with deterministic usernames:
      doctor1, doctor2, ..., doctorN
      password: doctor123
    """
    print(f"➡ Seeding {count} doctors...")
    doctors = []

    for i in range(1, count + 1):
        name = fake.name()
        specialization = random.choice(SPECIALIZATIONS)
        experience = random.randint(1, 25)
        about = f"Specialist in {specialization.lower()} with {experience} years of experience."

        username = f"doctor{i}"
        email = f"doctor{i}@hms.com"

        user = User(
            username=username,
            email=email,
            role="doctor",
            is_active=True,
        )
        user.set_password("doctor123")

        db.session.add(user)
        db.session.flush()  # get user.id

        doc = Doctor(
            id=user.id,
            full_name=name,
            specialization=specialization,
            experience_years=experience,
            about=about,
        )
        db.session.add(doc)
        doctors.append(doc)

    db.session.commit()
    print(f"✔ Seeded {len(doctors)} doctors.")
    return doctors


def seed_patients(count: int = 50):
    """
    Seed patients with deterministic usernames:
      patient1, patient2, ..., patientN
      password: patient123
    """
    print(f"➡ Seeding {count} patients...")
    patients = []

    for i in range(1, count + 1):
        full_name = fake.name()
        gender = random.choice(["Male", "Female", "Other"])
        dob = fake.date_of_birth(minimum_age=5, maximum_age=80).strftime("%Y-%m-%d")

        username = f"patient{i}"
        email = f"patient{i}@hms.com"

        user = User(
            username=username,
            email=email,
            role="patient",
            is_active=True,
        )
        user.set_password("patient123")

        db.session.add(user)
        db.session.flush()

        patient = Patient(
            id=user.id,
            full_name=full_name,
            gender=gender,
            dob=dob,
            address=fake.address().replace("\n", ", "),
            phone=fake.msisdn()[:10],
            height_cm=round(random.uniform(145, 185), 1),
            weight_kg=round(random.uniform(45, 95), 1),
            blood_group=random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]),
            is_disabled=random.choice([True, False, None]),
            profile_photo_url=None,
        )
        db.session.add(patient)
        patients.append(patient)

    db.session.commit()
    print(f"✔ Seeded {len(patients)} patients.")
    return patients


def random_slot_time():
    """
    Returns a string "HH:MM" between 09:00 and 17:00 in 30-min intervals.
    """
    start = dtime(9, 0)
    end = dtime(17, 0)
    slots = []

    current_dt = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    while current_dt < end_dt:
        slots.append(current_dt.time())
        current_dt += timedelta(minutes=30)

    t = random.choice(slots)
    return t.strftime("%H:%M")


def seed_appointments(doctors, patients, min_count: int = 300):
    print(f"➡ Seeding at least {min_count} appointments...")

    today = date.today()
    year = today.year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    total_days = (end_date - start_date).days + 1

    appts = []
    used_slots = set()  # (doctor_id, date_str, time_str) to avoid exact duplicates

    while len(appts) < min_count:
        doctor = random.choice(doctors)
        patient = random.choice(patients)

        # pick random date in year
        offset = random.randint(0, total_days - 1)
        appt_date = start_date + timedelta(days=offset)
        date_str = appt_date.strftime("%Y-%m-%d")

        time_str = random_slot_time()

        # check double-booking (per doctor, date, time)
        key = (doctor.id, date_str, time_str)
        if key in used_slots:
            continue  # skip, pick another combo
        used_slots.add(key)

        # status logic: future dates cannot be COMPLETED
        if appt_date > today:
            status = random.choices(
                ["BOOKED", "CANCELLED"],
                weights=[0.8, 0.2],
                k=1,
            )[0]
        else:
            status = random.choices(
                ["BOOKED", "COMPLETED", "CANCELLED"],
                weights=[0.4, 0.4, 0.2],
                k=1,
            )[0]

        reason = random.choice([
            "Fever and body pain",
            "Routine health checkup",
            "Follow-up visit",
            "Back pain since 2 weeks",
            "Headache and dizziness",
            "Diabetes follow-up",
            "Blood pressure check",
            "Skin rash and itching",
            "Cough and cold",
        ])

        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            date=date_str,
            time=time_str,
            status=status,
            reason=reason,
            created_at=datetime.combine(appt_date, dtime(hour=random.randint(8, 20)))
        )

        db.session.add(appt)
        appts.append(appt)

    db.session.commit()
    print(f"✔ Seeded {len(appts)} appointments.")
    return appts


def build_treatment_for_appointment(appt: Appointment) -> Treatment:
    """
    Build a Treatment that fits the CURRENT Treatment model:

    columns:
      - diagnosis
      - prescription  (we'll store medicines / dosage pattern here)
      - notes         (we'll store tests/precautions/visit type etc as text)
      - created_at
    """
    diagnosis = random.choice(DIAGNOSES)

    tests_done = ", ".join(random.sample(TESTS_LIST, k=random.randint(1, 3)))
    medicines = random.choice(MEDICINE_PATTERNS)
    precautions = random.choice(PRECAUTIONS_LIST)
    visit_type = random.choice(VISIT_TYPES)

    notes_parts = [
        f"Tests done: {tests_done}",
        f"Visit type: {visit_type}",
        f"Precautions: {precautions}",
    ]
    notes_text = " | ".join(notes_parts)

    return Treatment(
        appointment=appt,        # via relationship, sets appointment_id
        diagnosis=diagnosis,
        prescription=medicines,
        notes=notes_text,
        # created_at will be adjusted in seed_treatments()
    )


def seed_treatments(appointments):
    print("➡ Seeding treatments for COMPLETED appointments...")
    count = 0

    for appt in appointments:
        if appt.status != "COMPLETED":
            continue

        # 1–2 treatments per completed appointment
        n_treat = random.randint(1, 2)
        for _ in range(n_treat):
            t = build_treatment_for_appointment(appt)

            # created_at slightly after appointment date
            try:
                appt_date = datetime.fromisoformat(appt.date).date()
            except Exception:
                appt_date = date.today()

            t.created_at = datetime.combine(
                appt_date, dtime(hour=10)
            ) + timedelta(hours=random.randint(0, 6))

            db.session.add(t)
            count += 1

    db.session.commit()
    print(f"✔ Seeded {count} treatments.")


# ----------------------------
# Main
# ----------------------------

def main():
    app = create_app()
    with app.app_context():
        print("➡ Creating tables (if not exist)...")
        db.create_all()

        ensure_admin()
        wipe_non_admin_data()

        doctors = seed_doctors(15)
        patients = seed_patients(50)
        appointments = seed_appointments(doctors, patients, min_count=300)
        seed_treatments(appointments)


if __name__ == "__main__":
    main()
    print(">> Done seeding.")
