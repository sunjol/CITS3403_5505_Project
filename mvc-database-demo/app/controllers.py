from app import db
from app.models import ProjectGroup, Student


class ValidationError(Exception):
    pass


def list_groups():
    """Read operation: return all groups and their students."""
    groups = ProjectGroup.query.order_by(ProjectGroup.name.asc()).all()
    return [group.to_dict() for group in groups]


def create_group(name):
    """Create operation for the ProjectGroup model."""
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Group name is required.")

    group = ProjectGroup(name=clean_name)
    db.session.add(group)      # Stage the change, like git add.
    db.session.commit()        # Persist the change to SQLite.
    return group.to_dict()


def create_student(name, email, group_id):
    """Create operation for the Student model."""
    clean_name = (name or "").strip()
    clean_email = (email or "").strip().lower()

    if not clean_name or not clean_email or not group_id:
        raise ValidationError("Name, email and group are required.")

    group = ProjectGroup.query.get(group_id)
    if not group:
        raise ValidationError("Selected group does not exist.")

    student = Student(name=clean_name, email=clean_email, group=group)
    db.session.add(student)
    db.session.commit()
    return student.to_dict()


def update_student(student_id, name=None, email=None, group_id=None):
    """Update operation for a Student row."""
    student = Student.query.get_or_404(student_id)

    if name is not None:
        student.name = name.strip()
    if email is not None:
        student.email = email.strip().lower()
    if group_id is not None:
        group = ProjectGroup.query.get(group_id)
        if not group:
            raise ValidationError("Selected group does not exist.")
        student.group = group

    db.session.commit()
    return student.to_dict()


def delete_student(student_id):
    """Delete operation for a Student row."""
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return {"deleted_id": student_id}


def reset_demo_data():
    """Small seed function for teaching and repeated demos."""
    Student.query.delete()
    ProjectGroup.query.delete()

    alpha = ProjectGroup(name="Alpha")
    beta = ProjectGroup(name="Beta")
    db.session.add_all([alpha, beta])
    db.session.flush()

    db.session.add_all([
        Student(name="Ada Lovelace", email="ada@example.edu", group=alpha),
        Student(name="Grace Hopper", email="grace@example.edu", group=alpha),
        Student(name="Alan Turing", email="alan@example.edu", group=beta),
    ])
    db.session.commit()
    return list_groups()
