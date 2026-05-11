from flask import Blueprint, jsonify, render_template, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.controllers import (
    ValidationError,
    create_group,
    create_student,
    delete_student,
    list_groups,
    reset_demo_data,
    update_student,
)

main = Blueprint("main", __name__)


@main.get("/")
def index():
    # View route: render HTML using data from the model layer.
    return render_template("index.html", groups=list_groups())


@main.get("/api/groups")
def api_list_groups():
    # Read: this is equivalent to a SELECT query, handled via ORM.
    return jsonify(list_groups())


@main.post("/api/groups")
def api_create_group():
    try:
        payload = request.get_json() or {}
        return jsonify(create_group(payload.get("name"))), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A group with that name already exists."}), 400
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@main.post("/api/students")
def api_create_student():
    try:
        payload = request.get_json() or {}
        return jsonify(create_student(
            payload.get("name"),
            payload.get("email"),
            payload.get("group_id"),
        )), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A student with that email already exists."}), 400
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@main.patch("/api/students/<int:student_id>")
def api_update_student(student_id):
    try:
        payload = request.get_json() or {}
        return jsonify(update_student(
            student_id,
            name=payload.get("name"),
            email=payload.get("email"),
            group_id=payload.get("group_id"),
        ))
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "That email address is already used."}), 400
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@main.delete("/api/students/<int:student_id>")
def api_delete_student(student_id):
    return jsonify(delete_student(student_id))


@main.post("/api/reset")
def api_reset():
    return jsonify(reset_demo_data())
