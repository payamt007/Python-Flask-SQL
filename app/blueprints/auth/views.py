import base64

import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
)
from sqlalchemy import text

from app.db import engine

auth = Blueprint("auh", __name__)


def check_password(stored_password, provided_password):
    stored_password = base64.b64decode(stored_password.encode("utf-8"))

    # Verify the provided password against the stored hashed password
    return bcrypt.checkpw(provided_password.encode("utf-8"), stored_password)


@auth.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username},
        ).first()

        if not user:
            return jsonify({"msg": "Invalid username or password"}), 401

    stored_password = user[2]
    if not check_password(stored_password, password):
        return jsonify({"msg": "Invalid username or password"}), 401

    # Create a new token with the user id inside
    access_token = create_access_token(identity=user[1])
    return jsonify(access_token=access_token)
