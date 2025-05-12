import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
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
from models import Student, Statement, StatementChoice, StudentChoice, Teacher

# Route om een nieuwe student toe te voegen
@app.route("/add_student", methods=['GET', 'POST'])
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

@app.route("/statements")
def all_statements():
    statements = Statement.query.all()
    return jsonify([
        {
            "number": s.statement_number,
            "choices": [
                {"text": c.choice_text, "result": c.choice_result}
                for c in s.statement_choices
            ]
        }
        for s in statements
    ])

@app.route("/vragenlijst")
def vragenlijst():
        return render_template('vragenlijst.html')

@app.route('/api/student/<int:student_number>/statement', methods=['GET'])
def next_statement(student_number):
    student = Student.query.filter_by(student_number=student_number).first()
    if not student:
        return jsonify({'Error': 'Student not found'}), 404

    answered_statements = [choice.statement_id for choice in student.student_choices]

    next_statement = Statement.query \
        .filter(~Statement.statement_id.in_(answered_statements)) \
        .order_by(Statement.statement_number) \
        .first()

    if not next_statement:
        return jsonify({'Error': 'All statements have been answered'}), 404

    response = {
        'statement_number': next_statement.statement_number,
        'statement_choices': [
            {
                'choice_number': choice.choice_number,
                'choice_text': choice.choice_text
            }
            for choice in next_statement.statement_choices
        ]
    }
    print(next_statement.statement_choices)
    return jsonify(response), 200

# @app.route('api/student/<int:student_number>/statement/<int:statement_number>', methods=['POST'])
#     def submit_choice(student_number, statement_number):

@app.route('/api/student/<int:student_number>/statement/<int:statement_number>', methods=['POST'])
def submit_choice(student_number, statement_number):
    data = request.get_json()
    if not data or 'choice_number' not in data:
        return jsonify({"Error": "Missing 'choice_number' in request"}), 400

    choice_number = data['choice_number']

    student = Student.query.filter_by(student_number=student_number).first()
    if not student:
        return jsonify({"Error": "Student not found"}), 404

    statement = Statement.query.filter_by(statement_number=statement_number).first()
    if not statement:
        return jsonify({"Error": "Statement not found"}), 404

    choice = StatementChoice.query.filter_by(
        statement_id=statement.statement_id,
        choice_number=choice_number
    ).first()
    if not choice:
        return jsonify({"Error": "Choice not found for this statement"}), 404

    existing = StudentChoice.query.filter_by(
        student_id=student.student_id,
        statement_id=statement.statement_id
    ).first()

    if existing:
        existing.choice_number = choice_number
    else:
        new_choice = StudentChoice(
            student_id=student.student_id,
            statement_id=statement.statement_id,
            choice_number=choice_number
        )
        db.session.add(new_choice)

    db.session.commit()

    return jsonify({"result": "ok"}), 200

@app.route('/api/student/<int:student_number>/result', methods=['GET'])
# check of het studentnummer bestaat en haal de gegevens van de student op
def student_result(student_number):
    student = Student.query.filter_by(student_number=student_number).first()
    if not student:
        result = jsonify({"Error": "Student not found"}), 404
        return result
    # selecteer alle gegeven antwoorden van de student
    given_choices = student.student_choices

    # Een dictionary met alle letters die horen bij de keuzes
    mbti_letters = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}

    # Ga de ingevulde keuze van de specifieke student langs en haal daarvan de data op. Voeg daarna 1 punt toe aan de letter die hoort bij de gemaakte keuze. Doe dit voor elke gemaakte keuze.
    for choice in given_choices:
        response = StatementChoice.query.filter_by(statement_id=choice.statement_id, choice_number=choice.choice_number).first()
        print(response.choice_result)
        mbti_letters[response.choice_result] += 1

    # Lege result, deze wordt ingevuld door bij elke 2 letters te checken of 1 letter meer voorkomt dan de ander. Zo ja? Voeg die letter toe aan de string mbti_result. Zo niet? Voeg de andere letter toe.
    mbti_result = ""
    mbti_result += 'E' if mbti_letters['E'] >= mbti_letters['I'] else 'I'
    mbti_result += 'S' if mbti_letters['S'] >= mbti_letters['N'] else 'N'
    mbti_result += 'T' if mbti_letters['T'] >= mbti_letters['F'] else 'F'
    mbti_result += 'J' if mbti_letters['J'] >= mbti_letters['P'] else 'P'

    print(mbti_result)
    return jsonify({
        "student_number": student_number,
        "mbti_result": mbti_result,
        "counts": mbti_letters
    }), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        docent_username = request.form['docent_username']
        docent_password = request.form['docent_pass']
        docent = Teacher.query.filter_by(teacher_username=docent_username).first()
        if docent is None:
            return "Gebruiker niet gevonden"
        if not docent.check_password(docent_password):
            return "Wachtwoord onjuist"
        session['teacher_id'] = docent.teacher_id
        return redirect(url_for("admin_dashboard"))
    return render_template("login.html")
@app.route('/admin', methods=['GET'])
def admin_dashboard():
    return render_template('admin.html')

if __name__ == '__main__':
    with app.app_context():
        # import os
        # print("DB pad:", os.path.abspath("data/database.db"))
        db.create_all()
    app.run(debug=True)