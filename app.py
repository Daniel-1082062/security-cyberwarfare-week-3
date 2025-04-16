import os
from flask import Flask, render_template, request, redirect, url_for
from db import db
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'data', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    return 'Hello World!'

# importeer het Student model zodat ik een nieuwe entry in de tabel kan maken.
from models import Student

# Route om een nieuwe student toe te voegen
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    # Als de method POST is, maak een nieuwe rij in de tabel met als data de gegevens die in het formulier zijn ingevuld
    if request.method == 'POST':
        # definieer de waardes die in de kolommen moeten komen te staan
        student_number = request.form['student_number']
        name = request.form['name']
        class_name = request.form['class_name']

        # Maak een nieuwe rij in de tabel met de waardes die hierboven gedefinieerd zijn.
        new_student = Student(student_number=student_number, name=name, class_name=class_name)
        # Voeg de rij toe aan de database
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('index'))

# Als de method GET is, laat de pagina zien waarop je een nieuwe student kunt toevoegen
    return render_template('add_student.html')

if __name__ == '__main__':
    with app.app_context():
        import os
        print("DB pad:", os.path.abspath("data/database.db"))
        db.create_all()
    app.run(debug=True)