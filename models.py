from db import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC

# Maak de kolommen aan voor de Student tabel in de database
class Student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(7), unique=True, nullable=False)
    student_name = db.Column(db.String(120), nullable=False)
    student_class = db.Column(db.String(2), nullable=False)
    actiontype = db.Column(db.String(4))

    team_id = db.Column(db.Integer, db.ForeignKey('team.team_id', name='fk_student_team'), nullable=True)
    team = db.relationship('Team', backref='students')
    team_assigned_by_id = db.Column(db.Integer, db.ForeignKey('teacher.teacher_id', name='fk_student_team_assigned_by'), nullable=True)
    team_assigned_by = db.relationship('Teacher', foreign_keys=[team_assigned_by_id])


# Maak de klolommen aan voor de Statement tabel in de database
class Statement(db.Model):
    statement_id = db.Column(db.Integer, primary_key=True)
    statement_number = db.Column(db.Integer, unique=True, nullable=False)

    statement_choices = db.relationship('StatementChoice', backref='statement', cascade='all, delete-orphan')

# Maak de kolommen voor de StatementChoice tabel in de database
class StatementChoice(db.Model):
    choice_id = db.Column(db.Integer, primary_key=True)
    statement_id = db.Column(db.Integer, db.ForeignKey('statement.statement_id'), nullable=False)
    choice_number = db.Column(db.Integer, nullable=False)
    choice_text = db.Column(db.String(360), nullable=False)
    choice_result = db.Column(db.String(1), nullable=False)

# Maak de kolommen voor gemaakte keuzes van studenten
class StudentChoice(db.Model):
    student_choice_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    statement_id = db.Column(db.Integer, db.ForeignKey('statement.statement_id'), nullable=False)
    choice_number = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    student = db.relationship('Student', backref='student_choices')
    statement = db.relationship('Statement', backref='student_choices')

    statement_choice = db.relationship(
        'StatementChoice',
        primaryjoin="and_(StatementChoice.statement_id == foreign(StudentChoice.statement_id), "
                    "StatementChoice.choice_number == foreign(StudentChoice.choice_number))",
        uselist=False
    )

# Maak de kolommen voor de docenten tabel in de database
class Teacher(db.Model):
    teacher_id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    teacher_username = db.Column(db.String(120), nullable=False)
    teacher_password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, password):
        self.teacher_password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.teacher_password_hash, password)

class Team(db.Model):
    __tablename__ = 'team'
    team_id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(120), unique=True, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('teacher.teacher_id'))
    created_by = db.relationship('Teacher', backref='teams')