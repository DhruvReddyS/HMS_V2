# seed.py  — FINAL DEMO SEEDER
import random
import json
from datetime import datetime, timedelta, timezone

from app import create_app, db
from models import (
    User,
    Patient,
    Doctor,
    Appointment,
    Treatment,
    DoctorAvailability,
)

# -------------------------------------------------------------
# CONFIG: tweak counts & ranges here
# -------------------------------------------------------------
NUM_DOCTORS = 10          # doctor1..doctor10
NUM_PATIENTS = 60         # patient1..patient60
DAYS_BACK = 10            # days before today
DAYS_FORWARD = 20         # days after today
APPOINTMENT_BOOKING_DENSITY = 0.45  # % of available slots that become appointments

TIME_SLOTS = [
    "09:00", "09:30", "10:00", "10:30",
    "11:00", "11:30", "12:00",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30",
]

GENDERS = ["Male", "Female", "Other"]
BLOOD_GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]

SPECIALIZATIONS = [
    "General Physician",
    "Cardiologist",
    "Dermatologist",
    "Orthopedic Surgeon",
    "Pediatrician",
    "Neurologist",
    "ENT Specialist",
    "Psychiatrist",
    "Endocrinologist",
    "Pulmonologist",
]

DOCTOR_NAMES = [
    "Dr. Arjun Reddy",
    "Dr. Sneha Iyer",
    "Dr. Vivek Sharma",
    "Dr. Meera Nair",
    "Dr. Rahul Verma",
    "Dr. Kavya Rao",
    "Dr. Rohan Kulkarni",
    "Dr. Priya Menon",
    "Dr. Siddharth Jain",
    "Dr. Anjali Deshmukh",
]

PATIENT_FIRST_NAMES = [
    "Amit", "Ananya", "Ravi", "Priya", "Kiran", "Swathi", "Rohit", "Shreya",
    "Vivek", "Sneha", "Sanjay", "Divya", "Karthik", "Isha", "Nikhil", "Pooja",
    "Tarun", "Neha", "Aravind", "Deepa", "Harsha", "Lavanya", "Manoj", "Soumya",
    "Varun", "Keerthi", "Suresh", "Bhavya", "Sameer",
]

PATIENT_LAST_NAMES = [
    "Reddy", "Sharma", "Gupta", "Iyer", "Nair", "Verma", "Patel",
    "Kulkarni", "Menon", "Rao", "Jain", "Deshmukh", "Chowdary",
    "Singh", "Yadav",
]

REASONS = [
    "Fever and body pain",
    "Routine health checkup",
    "Chest discomfort",
    "Skin rashes and itching",
    "Back and knee pain",
    "Child vaccination",
    "Frequent headaches",
    "Anxiety and sleep issues",
    "Cough and breathing difficulty",
    "Diabetes follow-up",
    "High blood pressure follow-up",
    "Ear pain and discharge",
    "Throat infection",
]

# -------------------------------------------------------------
# Diagnoses, tests & prescriptions by specialization for realism
# -------------------------------------------------------------
DIAGNOSES_BY_SPEC = {
    "General Physician": [
        "Viral fever",
        "Upper respiratory tract infection",
        "Gastritis",
        "Migraine",
        "Acute gastroenteritis",
    ],
    "Cardiologist": [
        "Hypertension",
        "Stable angina",
        "Borderline dyslipidemia",
        "Palpitations – evaluation",
    ],
    "Dermatologist": [
        "Allergic dermatitis",
        "Acne vulgaris",
        "Fungal skin infection",
        "Urticaria",
    ],
    "Orthopedic Surgeon": [
        "Osteoarthritis knee",
        "Lumbar spondylosis",
        "Shoulder impingement syndrome",
        "Ankle sprain",
    ],
    "Pediatrician": [
        "Viral fever – pediatric",
        "Acute tonsillitis",
        "Bronchiolitis (mild)",
        "Routine vaccination visit",
    ],
    "Neurologist": [
        "Migraine without aura",
        "Tension-type headache",
        "Peripheral neuropathy – evaluation",
    ],
    "ENT Specialist": [
        "Acute otitis media",
        "Allergic rhinitis",
        "Pharyngitis",
        "Chronic sinusitis (mild)",
    ],
    "Psychiatrist": [
        "Generalized anxiety disorder",
        "Mild depression",
        "Insomnia",
    ],
    "Endocrinologist": [
        "Type 2 diabetes – uncontrolled",
        "Subclinical hypothyroidism",
        "PCOS – evaluation",
    ],
    "Pulmonologist": [
        "Mild asthma",
        "Acute bronchitis",
        "Suspected COVID-19 – mild",
    ],
}

TESTS_BY_DIAGNOSIS = {
    "Viral fever": ["CBC", "Malaria test", "Dengue NS1"],
    "Upper respiratory tract infection": ["CBC", "Throat swab if needed"],
    "Gastritis": ["H. pylori test", "LFT"],
    "Hypertension": ["ECG", "Kidney function test", "Lipid profile"],
    "Stable angina": ["ECG", "TMT", "2D Echo"],
    "Borderline dyslipidemia": ["Lipid profile"],
    "Allergic dermatitis": ["No specific test", "Allergy panel if needed"],
    "Acne vulgaris": ["No lab test needed"],
    "Osteoarthritis knee": ["X-ray knee AP & lateral"],
    "Lumbar spondylosis": ["X-ray lumbar spine"],
    "Viral fever – pediatric": ["CBC", "CRP"],
    "Acute tonsillitis": ["Throat swab", "CBC"],
    "Bronchiolitis (mild)": ["Chest X-ray if needed"],
    "Mild asthma": ["Pulmonary function test"],
    "Type 2 diabetes – uncontrolled": ["Fasting blood sugar", "HbA1c"],
    "Subclinical hypothyroidism": ["TSH", "Free T3/T4"],
}

PRESCRIPTION_LINES = [
    "Tab DOLO 650 mg | 1-1-1 | 5 days",
    "Tab PANTOP 40 mg | 1-0-0 | 10 days",
    "Syp Azee 200 mg | 5 ml 1-0-0 | 3 days",
    "Tab AZITHROMYCIN 500 mg | 1-0-0 | 3 days after food",
    "Tab CETIRIZINE 10 mg | 0-0-1 | 5 days",
    "Tab MONTELUKAST+LEVOCET | 0-0-1 | 10 days",
    "Tab NAPROXEN 250 mg | 1-0-1 | 5 days",
    "Tab METFORMIN 500 mg | 1-0-1 | 30 days",
    "Tab TELMISARTAN 40 mg | 1-0-0 | 30 days",
    "Inj VACCINE (per schedule)",
]

PRECAUTIONS = [
    "Drink plenty of water.",
    "Avoid oily and spicy food.",
    "Take adequate rest and sleep at least 7–8 hours.",
    "Check temperature every 6 hours and note it down.",
    "Avoid cold drinks and ice cream.",
    "Use mask in crowded places.",
    "Do regular walking for 30 minutes daily.",
    "Limit salt intake in food.",
    "Avoid screens 1 hour before sleeping.",
    "Practice deep breathing exercises twice daily.",
]

VISIT_TYPES = ["IN_PERSON", "ONLINE"]


# =============================================================
# CLEAR EXISTING DEMO DATA
# =============================================================
def clear_demo_data():
    print("⚠ Clearing existing demo doctors/patients, appointments, availability, treatments...")

    # Delete children first to satisfy FK constraints
    db.session.query(Treatment).delete()
    db.session.query(Appointment).delete()
    db.session.query(DoctorAvailability).delete()
    db.session.query(Patient).delete()
    db.session.query(Doctor).delete()
    # Remove all doctor & patient users but leave admin (role='admin') intact
    db.session.query(User).filter(User.role.in_(["doctor", "patient"])).delete(synchronize_session=False)

    db.session.commit()
    print("✔ Demo data cleared.")


# =============================================================
# CREATE DOCTORS & PATIENTS
# =============================================================
def ensure_doctors():
    doctors = []
    for i in range(1, NUM_DOCTORS + 1):
        username = f"doctor{i}"
        full_name = DOCTOR_NAMES[(i - 1) % len(DOCTOR_NAMES)]
        specialization = SPECIALIZATIONS[(i - 1) % len(SPECIALIZATIONS)]

        email = f"{username}@demo.hms.local"
        user = User(
            username=username,
            email=email,
            role="doctor",
            is_active=True,
        )
        user.set_password("doctor123")
        db.session.add(user)
        db.session.flush()  # get user.id

        doctor = Doctor(
            id=user.id,
            full_name=full_name,
            specialization=specialization,
            experience_years=random.randint(3, 25),
            about=f"{full_name} is an experienced {specialization.lower()} at Demo HMS.",
        )
        db.session.add(doctor)

        doctors.append(doctor)

    db.session.commit()
    return doctors


def random_patient_name():
    return f"{random.choice(PATIENT_FIRST_NAMES)} {random.choice(PATIENT_LAST_NAMES)}"


def random_phone():
    return "9" + "".join(str(random.randint(0, 9)) for _ in range(9))


def random_dob():
    # age between 5 and 75
    years_ago = random.randint(5, 75)
    today = datetime.now(timezone.utc).date()
    dob_date = today - timedelta(days=365 * years_ago + random.randint(0, 365))
    return dob_date.strftime("%Y-%m-%d")


def ensure_patients():
    patients = []
    for i in range(1, NUM_PATIENTS + 1):
        username = f"patient{i}"
        full_name = random_patient_name()

        email = f"{username}@demo.hms.local"
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
            gender=random.choice(GENDERS),
            dob=random_dob(),
            address="Some Demo Street, Hyderabad",
            phone=random_phone(),
            height_cm=round(random.uniform(150, 185), 1),
            weight_kg=round(random.uniform(45, 95), 1),
            blood_group=random.choice(BLOOD_GROUPS),
            is_disabled=random.choice([True, False, False, False]),  # mostly False
            # could be a static avatar URL in real app; keeping None is OK
            profile_photo_url=None,
        )
        db.session.add(patient)

        patients.append(patient)

    db.session.commit()
    return patients


# =============================================================
# AVAILABILITY: generate for each doctor & date window
# - includes holidays & partial unavailability
# =============================================================
def seed_availability(doctors):
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=DAYS_BACK)
    end_date = today + timedelta(days=DAYS_FORWARD)

    all_dates = [
        start_date + timedelta(days=i)
        for i in range((end_date - start_date).days + 1)
    ]

    for doctor in doctors:
        # choose some full-day holidays for this doctor
        doctor_holidays = set(random.sample(all_dates, k=max(1, len(all_dates) // 10)))

        for d in all_dates:
            date_str = d.strftime("%Y-%m-%d")

            if d in doctor_holidays:
                # Holiday: all slots unavailable
                for slot in TIME_SLOTS:
                    db.session.add(
                        DoctorAvailability(
                            doctor_id=doctor.id,
                            date=date_str,
                            time_slot=slot,
                            is_available=False,
                        )
                    )
                continue

            # working day: create slots, some available, some blocked
            for slot in TIME_SLOTS:
                # randomly decide if doctor works this slot
                is_available = random.random() > 0.2  # 80% of slots available
                db.session.add(
                    DoctorAvailability(
                        doctor_id=doctor.id,
                        date=date_str,
                        time_slot=slot,
                        is_available=is_available,
                    )
                )

    db.session.commit()


# =============================================================
# APPOINTMENTS + TREATMENTS:
# - Past days → mostly COMPLETED with Treatment
# - Today & future → BOOKED / some CANCELLED, mostly without Treatment
# =============================================================
def pick_diagnosis_for_doctor(doctor):
    diag_list = DIAGNOSES_BY_SPEC.get(doctor.specialization, None)
    if not diag_list:
        # fallback generic
        diag_list = ["General checkup", "Follow-up visit"]
    return random.choice(diag_list)


def generate_prescription_text():
    lines = random.sample(PRESCRIPTION_LINES, k=random.randint(2, 4))
    return "\n".join(lines)


def generate_tests_text(diagnosis):
    tests = TESTS_BY_DIAGNOSIS.get(diagnosis)
    if not tests:
        # generic tests
        tests = random.sample(
            [
                "CBC",
                "LFT",
                "KFT",
                "Fasting blood sugar",
                "HbA1c",
                "Chest X-ray",
                "ECG",
                "Lipid profile",
                "Thyroid profile",
            ],
            k=random.randint(1, 3),
        )
    return ", ".join(tests)


def seed_appointments_and_treatments(doctors, patients):
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=DAYS_BACK)
    end_date = today + timedelta(days=DAYS_FORWARD)

    all_dates = [
        start_date + timedelta(days=i)
        for i in range((end_date - start_date).days + 1)
    ]

    for d in all_dates:
        date_str = d.strftime("%Y-%m-%d")
        is_past = d < today

        for doctor in doctors:
            # get availability slots for that doctor & date that are available
            avail_slots = DoctorAvailability.query.filter_by(
                doctor_id=doctor.id,
                date=date_str,
                is_available=True,
            ).all()

            for slot_obj in avail_slots:
                time_slot = slot_obj.time_slot

                # randomly decide if this slot gets booked
                if random.random() > APPOINTMENT_BOOKING_DENSITY:
                    continue

                patient = random.choice(patients)
                reason = random.choice(REASONS)

                # Determine status based on date
                if is_past:
                    status = random.choice(["COMPLETED", "COMPLETED", "CANCELLED"])
                elif d == today:
                    status = random.choice(["BOOKED", "BOOKED", "CANCELLED"])
                else:
                    status = "BOOKED"

                created_at = datetime.now(timezone.utc) - timedelta(
                    days=random.randint(0, DAYS_BACK + 5)
                )

                appt = Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    date=date_str,
                    time=time_slot,
                    status=status,
                    reason=reason,
                    created_at=created_at,
                )
                db.session.add(appt)
                db.session.flush()  # to get appt.id

                # If appointment completed, add FULL Treatment
                if status == "COMPLETED":
                    diagnosis = pick_diagnosis_for_doctor(doctor)
                    prescription = generate_prescription_text()
                    tests_text = generate_tests_text(diagnosis)
                    precautions = " ".join(random.sample(PRECAUTIONS, k=2))

                    # Follow up after 7–30 days
                    follow_up_date = d + timedelta(days=random.randint(7, 30))
                    follow_up_str = follow_up_date.strftime("%Y-%m-%d")

                    # structured medicines_json – always filled
                    medicines_structured = [
                        {
                            "name": "DOLO 650",
                            "dose_pattern": "1-1-1",
                            "duration_days": 5,
                            "instruction": "After food",
                        },
                        {
                            "name": "PANTOP 40",
                            "dose_pattern": "1-0-0",
                            "duration_days": 10,
                            "instruction": "Before breakfast",
                        },
                    ]

                    treatment = Treatment(
                        appointment_id=appt.id,
                        diagnosis=diagnosis,
                        prescription=prescription,
                        notes="Patient advised as per prescription. Review if symptoms worsen.",
                        created_at=created_at + timedelta(hours=1),
                        visit_type=random.choice(VISIT_TYPES),
                        tests_text=tests_text,
                        precautions=precautions,
                        follow_up_date=follow_up_str,
                        medicines_json=json.dumps(medicines_structured),
                    )
                    db.session.add(treatment)

    db.session.commit()


# =============================================================
# MAIN ENTRY
# =============================================================
def seed_demo_data():
    print("➡ Seeding demo HMS data (doctors, patients, availability, appointments, treatments)...")

    clear_demo_data()

    doctors = ensure_doctors()
    print(f"✔ Created {len(doctors)} doctors (doctor1..doctor{len(doctors)})")

    patients = ensure_patients()
    print(f"✔ Created {len(patients)} patients (patient1..patient{len(patients)})")

    seed_availability(doctors)
    print("✔ Seeded doctor availability with realistic working days & holidays")

    seed_appointments_and_treatments(doctors, patients)
    print("✔ Seeded appointments & treatments across the last and upcoming days")

    print("✅ Demo data seeding complete!")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_demo_data()
