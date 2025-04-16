from app import db

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(7), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    class_name = db.Column(db.String(2), nullable=False)
