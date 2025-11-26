from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache

from config import Config
from models import db, User  # import User so we can seed admin

# Import ALL route functions
from routes.auth_routes import *
from routes.admin_routes import *
from routes.doctor_routes import *
from routes.patient_routes import *

cache = Cache()  # proper cache instance


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # -----------------------------
    # Extensions
    # -----------------------------
    db.init_app(app)
    JWTManager(app)
    cache.init_app(app)

    # -----------------------------
    # CORS (Vue @ localhost:5173)
    # -----------------------------
    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:5173"}},
        supports_credentials=True,
    )

    # =============================
    # AUTH ROUTES
    # =============================
    app.add_url_rule("/api/auth/register", view_func=register_user, methods=["POST"])
    app.add_url_rule("/api/auth/login", view_func=login_user, methods=["POST"])
    app.add_url_rule("/api/auth/me", view_func=get_current_user, methods=["GET"])

    # =============================
    # ADMIN ROUTES
    # =============================

    # Dashboard stats
    app.add_url_rule("/api/admin/stats", view_func=admin_stats, methods=["GET"])

    # Doctor management (admin side)
    app.add_url_rule("/api/admin/doctors", view_func=create_doctor, methods=["POST"])
    app.add_url_rule("/api/admin/doctors", view_func=list_doctors, methods=["GET"])
    app.add_url_rule(
        "/api/admin/doctors/<int:doctor_id>",
        view_func=get_doctor,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/admin/doctors/<int:doctor_id>",
        view_func=update_doctor,
        methods=["PUT"],
    )
    app.add_url_rule(
        "/api/admin/doctors/<int:doctor_id>",
        view_func=delete_doctor,
        methods=["DELETE"],
    )

    # Patient management (admin side)
    app.add_url_rule("/api/admin/patients", view_func=list_patients, methods=["GET"])
    app.add_url_rule(
        "/api/admin/patients/<int:patient_id>",
        view_func=get_patient,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/admin/patients/<int:patient_id>",
        view_func=update_patient,
        methods=["PUT"],
    )
    app.add_url_rule(
        "/api/admin/patients/<int:patient_id>",
        view_func=delete_patient,
        methods=["DELETE"],
    )

    # Appointments (admin side)
    app.add_url_rule(
        "/api/admin/appointments",
        view_func=admin_appointments,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/admin/appointments/<int:appointment_id>/status",
        view_func=admin_update_appointment_status,
        methods=["PUT"],
    )

    # =============================
    # DOCTOR ROUTES
    # =============================

    # Dashboard summary tiles (upcoming appts, today count, etc.)
    app.add_url_rule(
        "/api/doctor/dashboard-summary",
        view_func=doctor_dashboard_summary,
        methods=["GET"],
    )

    # List / filter doctor’s own appointments
    app.add_url_rule(
        "/api/doctor/appointments",
        view_func=doctor_appointments,
        methods=["GET"],
    )

    # Update status of a specific appointment (BOOKED → COMPLETED / CANCELLED)
    app.add_url_rule(
        "/api/doctor/appointments/<int:appt_id>/status",
        view_func=doctor_update_appointment_status,
        methods=["POST"],
    )

    # Save / update treatment details for an appointment
    app.add_url_rule(
        "/api/doctor/appointments/<int:appt_id>/treatment",
        view_func=doctor_save_treatment,
        methods=["POST"],
    )

    # Fetch full history of a particular patient (for this doctor)
    app.add_url_rule(
        "/api/doctor/patient-history/<int:patient_id>",
        view_func=doctor_patient_history,
        methods=["GET"],
    )

    # Doctor availability view (read-only – what slots are already blocked)
    app.add_url_rule(
        "/api/doctor/availability",
        view_func=doctor_availability,
        methods=["GET"],
    )

    # =============================
    # PATIENT ROUTES
    # =============================

    # Profile (view + update)
    app.add_url_rule(
        "/api/patient/profile",
        view_func=get_patient_profile,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/patient/profile",
        view_func=update_patient_profile,
        methods=["PUT"],
    )

    # Doctors + slots
    app.add_url_rule(
        "/api/patient/doctors",
        view_func=list_patient_doctors,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/patient/available-slots",
        view_func=patient_available_slots,
        methods=["GET"],
    )

    # Patient appointments (list + create)
    app.add_url_rule(
        "/api/patient/appointments",
        view_func=get_patient_appointments,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/patient/appointments",
        view_func=create_patient_appointment,
        methods=["POST"],
    )

    # Single appointment details
    app.add_url_rule(
        "/api/patient/appointments/<int:appointment_id>",
        view_func=get_single_patient_appointment,
        methods=["GET"],
    )

    # Cancel appointment
    app.add_url_rule(
        "/api/patient/appointments/<int:appointment_id>/cancel",
        view_func=cancel_patient_appointment,
        methods=["POST"],
    )

    # Visit history (appointments + treatments)
    app.add_url_rule(
        "/api/patient/history",
        view_func=get_patient_history,
        methods=["GET"],
    )

    # =============================
    # ROOT
    # =============================
    @app.route("/")
    def home():
        return jsonify({"message": "HMS Backend Running", "status": "OK"})

    return app


def create_default_admin():
    """Create a default admin user if none exists."""
    existing_admin = User.query.filter_by(role="admin").first()
    if existing_admin:
        print(f"✔ Admin already exists: {existing_admin.username}")
        return

    admin = User(
        username="admin",
        email="admin@hms.com",
        role="admin",
        is_active=True,
    )
    admin.set_password("admin123")  # default admin password

    db.session.add(admin)
    db.session.commit()

    print("✅ Default admin created:")
    print("   Username: admin")
    print("   Password: admin123")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("➡ Creating tables (if not exist)...")
        db.create_all()
        create_default_admin()

    app.run(debug=True)
