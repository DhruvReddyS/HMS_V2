from flask import request, jsonify
from models import db, User, Patient
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import timedelta


# ----------------------
# POST /api/auth/register
# Patient self-registration
# ----------------------
def register_user():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()

    if not username or not email or not password or not full_name:
        return jsonify({"message": "Missing required fields"}), 400

    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return jsonify({"message": "Username or email already exists"}), 400

    # Create base User
    user = User(
        username=username,
        email=email,
        role="patient",
        is_active=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Add Patient profile
    patient = Patient(
        id=user.id,
        full_name=full_name,
        phone=phone,
        address=address
    )
    db.session.add(patient)
    db.session.commit()

    return jsonify({"message": "Patient registered successfully"}), 201


# ----------------------
# POST /api/auth/login
# Common login for admin/doctor/patient
# ----------------------
def login_user():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid username or password"}), 401

    if not user.is_active:
        return jsonify({"message": "User is deactivated"}), 403

    # ✅ identity must be a simple type (string/int)
    # additional_claims can contain role or more metadata
    access_token = create_access_token(
        identity=str(user.id),              # MUST be string or int!
        additional_claims={"role": user.role},
        expires_delta=timedelta(hours=8)
    )

    return jsonify({
        "access_token": access_token,
        "id": user.id,
        "role": user.role,
        "username": user.username
    }), 200


# ----------------------
# GET /api/auth/me
# Returns the current logged-in user’s info
# ----------------------
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()   # this is now just the id
    claims = get_jwt()             # all claims, includes role

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": claims.get("role"),   # safe and consistent
        "is_active": user.is_active
    })
