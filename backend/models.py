from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id={self.id} username={self.username} role={self.role}>"


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    full_name = db.Column(db.String(120))
    gender = db.Column(db.String(20))
    dob = db.Column(db.String(20))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    blood_group = db.Column(db.String(10))
    is_disabled = db.Column(db.Boolean)
    profile_photo_url = db.Column(db.String(255))

    user = db.relationship("User", back_populates="patient_profile")
    appointments = db.relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    def to_profile_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.user.username if self.user else None,
            "email": self.user.email if self.user else None,
            "phone": self.phone,
            "gender": self.gender,
            "dob": self.dob,
            "address": self.address,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "blood_group": self.blood_group,
            "is_disabled": self.is_disabled,
            "profile_photo_url": self.profile_photo_url,
        }

    def __repr__(self):
        return f"<Patient id={self.id} full_name={self.full_name}>"


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    full_name = db.Column(db.String(120))
    specialization = db.Column(db.String(120))
    experience_years = db.Column(db.Integer)
    about = db.Column(db.String(255))

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
        return {
            "id": self.id,
            "full_name": self.full_name,
            "specialization": self.specialization,
            "experience_years": self.experience_years,
            "about": self.about,
        }

    def __repr__(self):
        return f"<Doctor id={self.id} full_name={self.full_name}>"


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="BOOKED")
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="appointments")
    doctor = db.relationship("Doctor", back_populates="appointments")
    treatments = db.relationship(
        "Treatment",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "doctor_id",
            "date",
            "time",
            name="uq_doctor_date_time",
        ),
    )

    def to_patient_dict(self):
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
            "status": self.status,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return (
            f"<Appointment id={self.id} "
            f"patient_id={self.patient_id} doctor_id={self.doctor_id}>"
        )


class Treatment(db.Model):
    __tablename__ = "treatments"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False)
    diagnosis = db.Column(db.String(255))
    prescription = db.Column(db.String(255))
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    visit_type = db.Column(db.String(20))
    tests_text = db.Column(db.String(255))
    precautions = db.Column(db.String(255))
    follow_up_date = db.Column(db.String(20))
    medicines_json = db.Column(db.Text)

    appointment = db.relationship("Appointment", back_populates="treatments")

    def to_dict(self):
        tests = None
        if self.tests_text:
            tests = [
                t.strip()
                for t in self.tests_text.replace("\r", "").replace("\n", ",").split(",")
                if t.strip()
            ]

        medicines_structured = None
        if self.medicines_json:
            try:
                medicines_structured = json.loads(self.medicines_json)
            except Exception:
                medicines_structured = None

        return {
            "id": self.id,
            "diagnosis": self.diagnosis,
            "prescription": self.prescription,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "visit_type": self.visit_type,
            "tests": tests,
            "tests_text": self.tests_text,
            "precautions": self.precautions,
            "follow_up_date": self.follow_up_date,
            "medicines": medicines_structured,
        }

    def __repr__(self):
        return f"<Treatment id={self.id} appointment_id={self.appointment_id}>"


class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time_slot = db.Column(db.String(10), nullable=False)
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
