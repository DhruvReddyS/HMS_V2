from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# ------------------------------------------------------
# USER MODEL (Admin / Doctor / Patient)
# ------------------------------------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)       # admin / doctor / patient
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 1–1 profiles
    patient_profile = db.relationship(
        "Patient",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    doctor_profile = db.relationship(
        "Doctor",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # password helpers
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id={self.id} username={self.username} role={self.role}>"


# ------------------------------------------------------
# PATIENT PROFILE (1–1 with User)
# ------------------------------------------------------
class Patient(db.Model):
    __tablename__ = "patients"

    # Same id as User.id (1–1 mapping)
    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    # Basic info
    full_name = db.Column(db.String(120))
    gender = db.Column(db.String(20))
    dob = db.Column(db.String(20))              # "YYYY-MM-DD" as string
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))

    # Extended health/profile info
    height_cm = db.Column(db.Float)             # e.g. 175.0
    weight_kg = db.Column(db.Float)             # e.g. 68.5
    blood_group = db.Column(db.String(10))      # e.g. "O+", "B-"
    is_disabled = db.Column(db.Boolean)         # physically challenged Y/N
    profile_photo_url = db.Column(db.String(255))

    # relationships
    user = db.relationship("User", back_populates="patient_profile")
    appointments = db.relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    def to_profile_dict(self):
        """
        Shape used by PatientDashboard / PatientProfile Vue pages.
        """
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.user.username if self.user else None,
            "email": self.user.email if self.user else None,
            "phone": self.phone,
            "gender": self.gender,
            "dob": self.dob,  # already "YYYY-MM-DD" string
            "address": self.address,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "blood_group": self.blood_group,
            "is_disabled": self.is_disabled,
            "profile_photo_url": self.profile_photo_url,
        }

    def __repr__(self):
        return f"<Patient id={self.id} full_name={self.full_name}>"


# ------------------------------------------------------
# DOCTOR PROFILE (1–1 with User)
# ------------------------------------------------------
class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    full_name = db.Column(db.String(120))
    specialization = db.Column(db.String(120))
    experience_years = db.Column(db.Integer)
    about = db.Column(db.String(255))

    # relationships
    user = db.relationship("User", back_populates="doctor_profile")
    appointments = db.relationship(
        "Appointment",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )
    availability_slots = db.relationship(
        "DoctorAvailability",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )

    def to_basic_dict(self):
        """
        Shape used by patient-side doctor dropdown / lists.
        """
        return {
            "id": self.id,
            "full_name": self.full_name,
            "specialization": self.specialization,
            "experience_years": self.experience_years,
            "about": self.about,
        }

    def __repr__(self):
        return f"<Doctor id={self.id} full_name={self.full_name}>"


# ------------------------------------------------------
# APPOINTMENTS
# ------------------------------------------------------
class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    # Proper foreign keys to profiles
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)

    # Keep as strings for simplicity
    date = db.Column(db.String(20), nullable=False)   # "YYYY-MM-DD"
    time = db.Column(db.String(20), nullable=False)   # "10:30" or "10:30 AM"

    status = db.Column(db.String(20), default="BOOKED")  # BOOKED / COMPLETED / CANCELLED
    reason = db.Column(db.String(255))                  # reason for visit (optional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ORM relationships
    patient = db.relationship("Patient", back_populates="appointments")
    doctor = db.relationship("Doctor", back_populates="appointments")
    treatments = db.relationship(
        "Treatment",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Optional: database-level guard so same doctor/date/time cannot be double-booked
        db.UniqueConstraint(
            "doctor_id",
            "date",
            "time",
            name="uq_doctor_date_time",
        ),
    )

    def to_patient_dict(self):
        """
        Shape for PatientAppointments.vue / patient history endpoints.
        """
        # Try to get a name priority: Doctor.full_name → User.username
        doctor_user = self.doctor.user if self.doctor and self.doctor.user else None
        doctor_name = None
        if self.doctor and self.doctor.full_name:
            doctor_name = self.doctor.full_name
        elif doctor_user:
            doctor_name = doctor_user.username

        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "doctor_name": doctor_name,
            "doctor_specialization": self.doctor.specialization if self.doctor else None,
            "appointment_date": self.date,
            "time_slot": self.time,
            "status": self.status,  # e.g. "BOOKED"
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return (
            f"<Appointment id={self.id} "
            f"patient_id={self.patient_id} doctor_id={self.doctor_id}>"
        )


# ------------------------------------------------------
# TREATMENTS (after appointment is completed)
# ------------------------------------------------------
class Treatment(db.Model):
    __tablename__ = "treatments"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False)

    # Core info
    diagnosis = db.Column(db.String(255))
    # raw medicines text like:
    # "DOLO 650 | 1-1-1 | 5 days\nPANTOP 40 | 1-0-1 | 7 days"
    prescription = db.Column(db.String(255))
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Extended visit details
    visit_type = db.Column(db.String(20))          # "IN_PERSON" / "ONLINE"
    tests_text = db.Column(db.String(255))         # free text, we parse into list in to_dict
    precautions = db.Column(db.String(255))        # lifestyle advice
    follow_up_date = db.Column(db.String(20))      # "YYYY-MM-DD" string

    # Optional legacy / future structured format (not used by new UI)
    medicines_json = db.Column(db.Text)

    appointment = db.relationship("Appointment", back_populates="treatments")

    def to_dict(self):
        """
        Shape returned by /patient/history for a single treatment record.
        Compatible with:
        - PatientVisitHistory.vue (uses prescription + tests_text + meta)
        - Older/legacy code (medicines_json if present)
        """
        # ---- tests_text → tests list ----
        tests = None
        if self.tests_text:
            # support both comma & newline separated
            tests = [
                t.strip()
                for t in self.tests_text.replace("\r", "").replace("\n", ",").split(",")
                if t.strip()
            ]

        # ---- legacy structured medicines (if you ever used medicines_json) ----
        medicines_structured = None
        if self.medicines_json:
            try:
                medicines_structured = json.loads(self.medicines_json)
            except Exception:
                medicines_structured = None

        return {
            "id": self.id,
            "diagnosis": self.diagnosis,
            # raw text used by patient history to render patterns
            "prescription": self.prescription,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,

            # visit meta
            "visit_type": self.visit_type,
            "tests": tests,                 # list[str] for chips
            "tests_text": self.tests_text,  # raw text for summary line
            "precautions": self.precautions,
            "follow_up_date": self.follow_up_date,

            # legacy / optional structured field
            "medicines": medicines_structured,
        }

    def __repr__(self):
        return f"<Treatment id={self.id} appointment_id={self.appointment_id}>"


# ------------------------------------------------------
# DOCTOR AVAILABILITY (per doctor, per date, per slot)
# ------------------------------------------------------
class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)

    # Specific date this availability applies to
    date = db.Column(db.String(20), nullable=False)      # "YYYY-MM-DD"

    # Slot time; must match whatever you use in DEFAULT_TIME_SLOTS
    time_slot = db.Column(db.String(10), nullable=False)  # "09:00", "09:30", ...

    # If False → doctor is not working in this specific slot on this date
    is_available = db.Column(db.Boolean, default=True)

    doctor = db.relationship("Doctor", back_populates="availability_slots")

    __table_args__ = (
        db.UniqueConstraint(
            "doctor_id",
            "date",
            "time_slot",
            name="uq_doctor_date_slot",
        ),
    )

    def __repr__(self):
        return (
            f"<DoctorAvailability doctor_id={self.doctor_id} "
            f"date={self.date} time_slot={self.time_slot} "
            f"available={self.is_available}>"
        )
