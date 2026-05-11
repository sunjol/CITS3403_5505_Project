from app import db


class ProjectGroup(db.Model):
    """Model: one row in the project_group table."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

    # One group has many students. back_populates keeps both sides in sync.
    students = db.relationship(
        "Student",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self):
        """Helper method: keeps display logic out of routes."""
        return {
            "id": self.id,
            "name": self.name,
            "students": [
                student.to_dict(include_group=False) for student in self.students
            ],
        }

    def __repr__(self):
        return f"<ProjectGroup {self.name}>"


class Student(db.Model):
    """Model: one row in the student table."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # Foreign key: links each student to a ProjectGroup.id value.
    group_id = db.Column(db.Integer, db.ForeignKey("project_group.id"), nullable=False)

    # Relationship: lets Python use student.group instead of manual SQL joins.
    group = db.relationship("ProjectGroup", back_populates="students")

    def to_dict(self, include_group=True):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "group_id": self.group_id,
        }
        if include_group:
            data["group"] = self.group.name if self.group else None
        return data

    def __repr__(self):
        return f"<Student {self.email}>"
