from db import db

# Creating the columns for the Student table in the database
class Student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(7), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    class_name = db.Column(db.String(2), nullable=False)

# Creating the columns for the Statement table in the database
class Statement(db.Model):
    statement_id = db.Column(db.Integer, primary_key=True)
    statement_number = db.Column(db.Integer, unique=True, nullable=False)
    statement_choices = db.relationship('Statement_choice', backref='statement', cascade='all, delete-orphan')

# Creating the columns for the StatementChoice table in the database
class StatementChoice(db.Model):
    choice_id = db.Column(db.Integer, primary_key=True)
    statement_id = db.Column(db.Integer, db.foreign_key('statement_id'), nullable=False)
    choice_number = db.Column(db.Integer, nullable=False)
    choice_text = db.Column(db.String(360), nullable=False)
    choice_result = db.Column(db.String(1), nullable=False)