from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache

from config import Config
from models import db, User

from routes.auth_routes import *
from routes.admin_routes import *
from routes.doctor_routes import *
from routes.patient_routes import *

cache = Cache()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    JWTManager(app)
    cache.init_app(app)

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

    app.add_url_rule("/api/auth/register", view_func=register_user, methods=["POST"])
    app.add_url_rule("/api/auth/login", view_func=login_user, methods=["POST"])
    app.add_url_rule("/api/auth/me", view_func=get_current_user, methods=["GET"])

    app.add_url_rule("/api/admin/stats", view_func=admin_stats, methods=["GET"])
    app.add_url_rule(
        "/api/admin/reports-analytics",
        view_func=admin_reports_analytics,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/admin/monthly-report",
        view_func=admin_monthly_report,
        methods=["GET"],
    )

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

    app.add_url_rule(
        "/api/doctor/dashboard-summary",
        view_func=doctor_dashboard_summary,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/doctor/appointments",
        view_func=doctor_list_appointments,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/doctor/appointments/<int:appointment_id>/status",
        view_func=doctor_update_appointment_status,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/doctor/appointments/<int:appointment_id>/treatment",
        view_func=doctor_save_treatment,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/doctor/appointments/<int:appointment_id>/treatment",
        view_func=doctor_get_treatment,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/doctor/availability",
        view_func=doctor_availability,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/doctor/availability/toggle",
        view_func=doctor_toggle_availability,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/doctor/availability/bulk",
        view_func=doctor_update_availability,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/doctor/patient-history",
        view_func=doctor_patient_history,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/doctor/profile",
        view_func=doctor_get_profile,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/doctor/profile",
        view_func=doctor_update_profile,
        methods=["PUT"],
    )
    app.add_url_rule(
        "/api/doctor/my-patients",
        view_func=doctor_my_patients,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/doctor/stats",
        view_func=doctor_stats,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/doctor/monthly-report",
        view_func=doctor_monthly_report,
        methods=["GET"],
    )

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
    app.add_url_rule(
        "/api/patient/appointments/<int:appointment_id>",
        view_func=get_single_patient_appointment,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/patient/appointments/<int:appointment_id>/cancel",
        view_func=cancel_patient_appointment,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/patient/history",
        view_func=get_patient_history,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/patient/history/export-csv",
        view_func=patient_history_export_csv,
        methods=["GET"],
    )
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

    @app.route("/")
    def home():
        return jsonify({"message": "HMS Backend Running", "status": "OK"})

    @app.route("/api/health")
    def health():
        try:
            db.session.execute("SELECT 1")
            db_ok = True
        except Exception:
            db_ok = False

        cache_ok = True
        try:
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
    existing_admin = User.query.filter_by(role="admin").first()
    if existing_admin:
        print(f"Admin already exists: {existing_admin.username}")
        return

    admin = User(
        username="admin",
        email="admin@hms.com",
        role="admin",
        is_active=True,
    )
    admin.set_password("admin123")

    db.session.add(admin)
    db.session.commit()

    print("Default admin created:")
    print("Username: admin")
    print("Password: admin123")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("➡ Creating tables (if not exist)...")
        db.create_all()
        create_default_admin()

    app.run(debug=True)
