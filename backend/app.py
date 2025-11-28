from flask import Flask, jsonify
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

# Global cache instance used by cache_utils.cached / cache_delete_pattern
cache = Cache()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # -----------------------------
    # Extensions
    # -----------------------------
    db.init_app(app)
    JWTManager(app)
    cache.init_app(app)  # backed by Redis as per Config

    # -----------------------------
    # CORS (Vue dev @ :5173)
    # -----------------------------
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ]
            }
        },
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

    # -----------------------------
    # Doctor management (admin side)
    # -----------------------------
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

    # -----------------------------
    # Patient management (admin side)
    # -----------------------------
    app.add_url_rule(
        "/api/admin/patients",
        view_func=list_patients,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/admin/patients",
        view_func=create_patient,
        methods=["POST"],
    )
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

    # -----------------------------
    # Appointments (admin side)
    # -----------------------------
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
        view_func=doctor_list_appointments,
        methods=["GET"],
    )

    # Update status of a specific appointment (BOOKED → COMPLETED / CANCELLED)
    app.add_url_rule(
        "/api/doctor/appointments/<int:appointment_id>/status",
        view_func=doctor_update_appointment_status,
        methods=["POST"],
    )

    # Save / update treatment details for an appointment
    app.add_url_rule(
        "/api/doctor/appointments/<int:appointment_id>/treatment",
        view_func=doctor_save_treatment,
        methods=["POST"],
    )

    # Get treatment details for an appointment (auto-fill on doctor side)
    app.add_url_rule(
        "/api/doctor/appointments/<int:appointment_id>/treatment",
        view_func=doctor_get_treatment,
        methods=["GET"],
    )

    # Doctor availability view (7-day grid)
    app.add_url_rule(
        "/api/doctor/availability",
        view_func=doctor_availability,
        methods=["GET"],
    )

    # Toggle a single slot (click on cell)
    app.add_url_rule(
        "/api/doctor/availability/toggle",
        view_func=doctor_toggle_availability,
        methods=["POST"],
    )

    # Bulk update a day's slots (full day off)
    app.add_url_rule(
        "/api/doctor/availability/bulk",
        view_func=doctor_update_availability,
        methods=["POST"],
    )

    # Fetch full history of a particular patient (for this doctor)
    app.add_url_rule(
        "/api/doctor/patient-history",
        view_func=doctor_patient_history,
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

    # ✅ Direct CSV export (sync)
    app.add_url_rule(
        "/api/patient/history/export-csv",
        view_func=patient_history_export_csv,
        methods=["GET"],
    )

    # ==========================================
    # PATIENT EXPORT HISTORY (CSV via Celery)
    # ==========================================
    app.add_url_rule(
        "/api/patient/export-history",
        view_func=patient_export_history,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/patient/export-history/status/<task_id>",
        view_func=patient_export_history_status,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/patient/export-history/download/<task_id>",
        view_func=patient_export_history_download,
        methods=["GET"],
    )

    # =============================
    # HEALTH / ROOT
    # =============================
    @app.route("/")
    def home():
        return jsonify({"message": "HMS Backend Running", "status": "OK"})

    @app.route("/api/health")
    def health():
        """
        Simple health check for DB + cache (Redis).
        Perfect to show in viva and for quick infra debugging.
        """
        try:
            db.session.execute("SELECT 1")
            db_ok = True
        except Exception:
            db_ok = False

        cache_ok = True
        try:
            # backend-specific; for RedisCache this will touch Redis
            cache.set("healthcheck", "ok", timeout=5)
            if cache.get("healthcheck") != "ok":
                cache_ok = False
        except Exception:
            cache_ok = False

        return jsonify({
            "status": "OK" if (db_ok and cache_ok) else "DEGRADED",
            "db": db_ok,
            "cache": cache_ok,
        }), 200 if (db_ok and cache_ok) else 503

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
