import json
from app import app, db
from models import Student

# Laad het JSON bestand in
with app.app_context():
    with open('data/students.json', 'r') as f:
        students = json.load(f)

    for item in students:
        number = item['student_number']

        # Check of het student nummer al in de database staat,
        existing = Student.query.filter_by(student_number=number).first()
        if existing:
            print(f"Student {number} bestaat al, overslaan.")
            continue

        student = Student(
            student_number=number,
            student_name=item['student_name'],
            student_class=item['student_class']
        )
        db.session.add(student)

    db.session.commit()
    print(f"{len(data)} studenten geïmporteerd.")

