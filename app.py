import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from db import db
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'data', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# importeer het Student model zodat ik een nieuwe entry in de tabel kan maken.
from models import Student, Statement, StatementChoice, StudentChoice, Teacher, Team

# Route om een nieuwe student toe te voegen
@app.route("/beheer/student/toevoegen", methods=['GET', 'POST'])
def add_student():
    docent = get_logged_in_teacher()
    if not docent:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return redirect(url_for('studenten_dashboard'))

    # definieer de waardes die in de kolommen moeten komen te staan
    student_number = request.form['student_number']
    student_name = request.form['student_name']
    student_class = request.form['student_class']

    existing = Student.query.filter_by(student_number=student_number).first()
    if existing:
        # return "Studentnummer bestaat al", 400
        error = "Studentnummer bestaat al."
        studenten = Student.query.all()
        return render_template("studentenbeheer.html", studenten=studenten, error=error)

    # Maak een nieuwe rij in de tabel met de waardes die hierboven gedefinieerd zijn.
    new_student = Student(student_number=student_number, student_name=student_name, student_class=student_class)
    # Voeg de rij toe aan de database
    db.session.add(new_student)
    db.session.commit()
    return redirect(url_for('studenten_dashboard'))


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

@app.route("/")
def vragenlijst():
        return render_template('vragenlijst.html')

@app.route('/api/student/<int:student_number>/statement', methods=['GET'])
def next_statement(student_number):
    # Vraag de student op aan de hand van het studentnummer. Is de student niet te vinden? Geef een error.
    student = Student.query.filter_by(student_number=student_number).first()
    if not student:
        return jsonify({'Error': 'Student not found'}), 404

    # Check of de student al een actiontype heeft, zo ja. Geef een 403 die laat weten dat de test al gemaakt is.
    if student.actiontype:
        return jsonify({'Error': 'De test is al voltooid. Het is niet mogelijk deze opnieuw te maken.'}), 403

    # Maak een list met de statements die de student al beantwoord heeft door alle statement_id's te verzamelen uit de tabel met gemaakte keuzes van de student.
    answered_statements = [choice.statement_id for choice in student.student_choices]

    # Vraag het eerstvolgende onbeantwoorde statement op door te filteren op 'komt niet voor in de list 'answered_statements'.
    next_statement = Statement.query \
        .filter(~Statement.statement_id.in_(answered_statements)) \
        .order_by(Statement.statement_number) \
        .first()

    # Komt er geen resultaat uit het oprvragen van de eerstvolgende statement? Geef een 404 response en laat weten dat alle statements al beantwoord zijn.
    if not next_statement:
        return jsonify({'Error': 'All statements have been answered'}), 404

    # Maak een dictionary met de gegevens van het opgevraagde statement. Convert deze daarna met jsonify naar JSON en geef dit als response samen met 200 (OK).
    response = {
        'statement_number': next_statement.statement_number,
        'student_name': student.student_name,
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
    # Kijk of er een choice_number in de opgeroepen data aanwezig is. Zo niet: Geef een error.
    data = request.get_json()
    if not data or 'choice_number' not in data:
        return jsonify({"Error": "Missing 'choice_number' in request"}), 400

    choice_number = data['choice_number']

    # Check of er een student met een studentnummer bestaat en koppel deze aan student, zo niet, geef een error.
    student = Student.query.filter_by(student_number=student_number).first()
    if not student:
        return jsonify({"Error":
                            "Student not found"}), 404

    # Check of er een statement met het statementnummer bestaat en koppel deze aan statement. Zo niet, geef een error.
    statement = Statement.query.filter_by(statement_number=statement_number).first()
    if not statement:
        return jsonify({"Error": "Statement not found"}), 404

    # Zoek de gemaakte keuze op aan de hand van het statement_id en het choice_number en koppel deze data aan choice.
    choice = StatementChoice.query.filter_by(
        statement_id=statement.statement_id,
        choice_number=choice_number
    ).first()
    # Is de gemaakte keuze niet te vinden? Geef dan een error.
    if not choice:
        return jsonify({"Error": "Choice not found for this statement"}), 404

    # Check of de student de vraag al een keer eerder beantwoord heeft.
    existing = StudentChoice.query.filter_by(
        student_id=student.student_id,
        statement_id=statement.statement_id
    ).first()

    # Heeft de student de vraag al een keer eerder beantwoord? Overschrijf dan de eerder gemaakt ekeuze.
    if existing:
        existing.choice_number = choice_number\
    # Heeft de student de vraag nog niet eerder beantwoord? Maak dan een nieuwe entry in de tabel met gemaakte keuzes.
    else:
        new_choice = StudentChoice(
            student_id=student.student_id,
            statement_id=statement.statement_id,
            choice_number=choice_number
        )
        db.session.add(new_choice)

    # Commit de nieuwe data naar de database en geef een 200 response (OK!)
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

    # Pas de actiontype van de student aan in de database
    student.actiontype = mbti_result
    db.session.commit()

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
        return redirect(url_for("beheer_dashboard"))
    return render_template("login.html", error=request.args.get('error'))

@app.route('/beheer', methods=['GET'])
def beheer_dashboard():
    # Controleer of er een teacher_id in de session is, zo ja leid door naar de admin pagina
    if session.get('teacher_id'):
        docent = Teacher.query.get(session['teacher_id'])
        is_admin = docent.is_admin
        return render_template('beheer.html', docent=docent, is_admin=is_admin)
    # Zit er geen teacher_id in de session? Leid dan door naar de loginpagina.
    else:
        return redirect(url_for('login'))

@app.route('/admin/', methods=['POST', 'GET'])
def admin_dashboard():
    # # Check of er een teacher_id in de session is
    # teacher_id = session.get('teacher_id')
    #
    # # Is er geen teacher_id in de session? Leid terug naar de loginpagina
    # if not teacher_id:
    #     return redirect(url_for('login'))
    #
    # # docent = Teacher.query.get('teacher_id')
    # docent = Teacher.query.get(int(session['teacher_id']))

    docent = get_logged_in_teacher()

    docenten = Teacher.query.all()

    # Dubbelcheck: zit er geen teacher_id in de session? Geef een error. Doe hetzelfde als de docent geen admin is.

    # if not docent or not docent.is_admin:
    #     print(docent)
    #     print(docent.is_admin)
    #     return redirect(url_for('login', error='geen_toegang'))

    if not docent:
        session.clear()
        return redirect(url_for('login', error='geen_toegang'))

    if not docent.is_admin:
        return redirect(url_for('beheer_dashboard', error='geen_toegang'))

    # Zit er een teacher_id in de session én is de docent een admin? Leid door naar de docentbeheer pagina.
    else:
        return render_template ('admin.html', docent=docent, docenten=docenten)

@app.route('/admin/toggle_admin/<docent_id>', methods=['POST'])
def toggle_admin(docent_id):
    # # Check of de gebruiker een docent is
    # teacher_id = session.get('teacher_id')
    # if not teacher_id:
    #     return redirect(url_for('login'))
    #
    # # Check of de docent een admin is (en check nogmaals of de gebruiker een docent is)
    # docent_self = Teacher.query.get(int(teacher_id))

    docent_self = get_logged_in_teacher()

    if not docent_self or not docent_self.is_admin:
        return redirect(url_for('login', error='geen_toegang'))

    # Haal de docent op. Als de teacher niet gevonden wordt, geef een error
    docent = Teacher.query.get(int(docent_id))
    if not docent:
        return "Docent niet gevonden", 404

    # Maak de nieuwe waarde van is_admin het omgekeerde van de huidige waarde van is_admin
    docent.is_admin = not docent.is_admin
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_teacher', methods=['POST'])
def add_teacher():
    # # Check of de gebruiker een docent is
    # teacher_id = session.get('teacher_id')
    # if not teacher_id:
    #     return redirect(url_for('login'))
    #
    # # Check of de docent een admin is (en check nogmaals of de gebruiker een docent is)
    # docent_self = Teacher.query.get(int(teacher_id))

    docent_self = get_logged_in_teacher()

    if not docent_self or not docent_self.is_admin:
        return redirect(url_for('login', error='geen_toegang'))

    # Haal de waardes uit het formulier op
    docent_name = request.form['docent_name']
    docent_username = request.form['docent_username']
    docent_password = request.form['docent_password']
    is_admin = 'is_admin' in request.form

    # Controleer of gebruikersnaam al bestaat
    existing = Teacher.query.filter_by(teacher_username=docent_username).first()
    if existing:
        error = "Gebruikersnaam bestaat al"
        docenten = Teacher.query.all()
        return render_template('admin.html', docent=docent_self, docenten=docenten, error=error)

    # Maak een nieuwe entry in de tabel met docenten met de opgehaalde en maak een gehashed wachtwoord met het ingevulde wachtwoord uit het formulier
    new_teacher = Teacher(teacher_name=docent_name, teacher_username=docent_username, is_admin=is_admin)
    new_teacher.set_password(docent_password)

    # Voeg de nieuwe docent toe aan de database en sla de database op
    db.session.add(new_teacher)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_teacher/<teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    # # Check of de gebruiker een docent is
    # current_user_id = session.get('teacher_id')
    # if not current_user_id:
    #     return redirect(url_for('login'))
    #
    # # Check of de docent een admin is (en check nogmaals of de gebruiker een docent is)
    # docent_self = Teacher.query.get(int(current_user_id))

    docent_self = get_logged_in_teacher()

    if not docent_self or not docent_self.is_admin:
        return redirect(url_for('login', error='geen_toegang'))


    delete_teacher = Teacher.query.get(int(teacher_id))

    if not delete_teacher:
        return redirect(url_for('admin_dashboard', error='delete_docent_not_found'))

    if delete_teacher.teacher_id == docent_self.teacher_id:
        return redirect(url_for('admin_dashboard', error='geen_self_delete'))

    db.session.delete(delete_teacher)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/beheer/studenten', methods=['GET'])
def studenten_dashboard():
    # # Check of de gebruiker een docent is
    # teacher_id = session.get('teacher_id')
    # if not teacher_id:
    #     return redirect(url_for('login'))
    #
    # # Check of de docent een admin is (en check nogmaals of de gebruiker een docent is)
    # docent_self = Teacher.query.get(int(teacher_id))

    docent = get_logged_in_teacher()

    if not docent:
        return redirect(url_for('login'))

    # Vraag alle studenten op en check of er filters zijn ingevuld
    class_filter = request.args.get('class')
    team_filter = request.args.get('team')
    has_team_filter = request.args.get('has_team')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query=Student.query

    # Als er filters zijn, voeg deze toe aan de query
    if class_filter:
        query = query.filter_by(student_class=class_filter)
    if team_filter:
        try:
            team_id = int(team_filter)
            query = query.filter_by(team_id=team_id)
        except ValueError:
            pass
    if has_team_filter == "met":
        query = query.filter(Student.team_id.isnot(None))
    if has_team_filter == "zonder":
        query = query.filter(Student.team_id.is_(None))

    # studenten = query.all()

    studenten_pagination = query.order_by(Student.student_id).paginate(page=page, per_page=per_page)
    studenten = studenten_pagination.items

    klassen = db.session.query(Student.student_class).distinct().all()
    teams = Team.query.all()

    return render_template('studentenbeheer.html', studenten=studenten, docent=docent, klassen=[k[0] for k in klassen], teams=teams, class_filter=class_filter, team_filter=team_filter, has_team_filter=has_team_filter, pagination=studenten_pagination)

@app.template_filter('localtime')
def localtime_filter(utc_dt):
    if utc_dt is None:
        return ''
    # Verander de tijd naar GMT+2
    return (utc_dt + timedelta(hours=2)).strftime('%d-%m-%Y %H:%M')

@app.route('/beheer/student/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    # # Check of de gebruiker een docent is
    # teacher_id = session.get('teacher_id')
    # if not teacher_id:
    #     return redirect(url_for('login'))
    #
    # # Check of de docent een admin is (en check nogmaals of de gebruiker een docent is)
    # docent_self = Teacher.query.get(int(teacher_id))

    docent = get_logged_in_teacher()

    if not docent:
        return redirect(url_for('login'))

    student = Student.query.get(student_id)
    if not student:
        if not student:
            return redirect(url_for('studenten_dashboard', error='student_niet_gevonden'))

    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('studenten_dashboard'))

@app.route("/beheer/teams", methods=["GET"])
def teams_dashboard():
    # # Check of de gebruiker een docent is
    # teacher_id = session.get('teacher_id')
    # if not teacher_id:
    #     return redirect(url_for('login'))
    #
    # # Check of de docent een admin is (en check nogmaals of de gebruiker een docent is)
    # docent_self = Teacher.query.get(int(teacher_id))

    docent = get_logged_in_teacher()

    if not docent:
        return redirect(url_for('login'))

    # docent = Teacher.query.get(session['teacher_id'])
    teams = Team.query.all()
    return render_template('teambeheer.html', docent=docent, teams=teams)

@app.route("/beheer/teams/delete/<int:team_id>", methods=["POST"])
def delete_team(team_id):
    # teacher_id = session.get('teacher_id')
    # docent = Teacher.query.get(teacher_id)

    docent = get_logged_in_teacher()

    # Check of de gebruiker een docent is
    if not docent:
        return redirect(url_for('login'))

    # Check of het team met dat id bestaat
    team = Team.query.get(team_id)
    if not team:
        return redirect(url_for("teams_dashboard", error="team_niet_gevonden"))

    # Verwijder het team uit de database en sla dit op
    db.session.delete(team)
    db.session.commit()
    return redirect(url_for("teams_dashboard"))

@app.route("/beheer/teams/toevoegen", methods=["POST"])
def add_team():
    # teacher_id = session.get('teacher_id')
    # docent = Teacher.query.get(teacher_id)

    docent = get_logged_in_teacher()

    # Check of de gebruiker docent is
    if not docent:
        return "Geen toegang", 403

    # Haal de naam van het nieuwe team op uit de form
    team_name = request.form['team_name']

    # Check of de naam van het team al bestaat
    existing = Team.query.filter_by(team_name=team_name).first()
    if existing:
        error = "Deze teamnaam bestaat al."
        teams = Team.query.all()
        return render_template("teambeheer.html", docent=docent, teams=teams, error=error)

    # Maak een nieuw team aan met de opgehaalde gegevens en sla deze op in de databse
    new_team = Team(team_name=team_name, created_by=docent)
    db.session.add(new_team)
    db.session.commit()
    return redirect(url_for("teams_dashboard"))

@app.route("/beheer/student/<int:student_id>", methods=["GET"])
def student_details(student_id):
    docent = get_logged_in_teacher()

    # Check of de gebruiker docent is
    if not docent:
        return redirect(url_for('login'))

    student = Student.query.get(student_id)
    if not student:
        return "Student niet gevonden", 404

    teams = Team.query.all()
    return render_template("student_details.html", student=student, teams=teams, docent=docent)

@app.route("/beheer/student/<int:student_id>/team", methods=["POST"])
def wijzig_student_team(student_id):
    docent = get_logged_in_teacher()
    if not docent:
        return redirect(url_for('login'))

    student = Student.query.get(student_id)
    if not student:
        return "Student niet gevonden", 404

    # Haal de gekozen team_id op uit het formulier
    team_id = request.form.get("team_id")

    # Koppel student aan het gekozen team, of ontkoppel bij lege waarde
    if team_id:
        team = Team.query.get(int(team_id))
        if not team:
            return "Team niet gevonden", 404
        student.team = team
        student.team_assigned_by = docent
    else:
        student.team = None  # Team ontkoppelen
        student.team_assigned_by = None

    db.session.commit()
    return redirect(url_for('student_details', student_id=student.student_id))

@app.route('/beheer/student/<int:student_id>/bewerken', methods=['GET', 'POST'])
def bewerk_student(student_id):
    docent = get_logged_in_teacher()
    if not docent:
        return redirect(url_for('login'))

    student = Student.query.get(student_id)
    if not student:
        return "Student niet gevonden", 404

    teams = Team.query.all()

    if request.method == 'POST':
        # Haal de data op uit het formulier
        student.student_name = request.form['student_name']
        student.student_class = request.form['student_class']
        # Check hier eerst of er een team is geselecteerd
        team_id = request.form.get('team_id')

        # Als er een team geselecteerd is, koppel deze dan, zo niet? Laat dit veld leeg.
        if team_id:
            student.team = Team.query.get(int(team_id))
            student.team_assigned_by = docent
        else:
            student.team = None
            student.team_assigned_by = None

        # Sla op
        db.session.commit()
        return redirect(url_for('student_details', student_id=student.student_id, saved='1'))

    return render_template('student_details.html', student=student, teams=teams, docent=docent)

@app.route('/logout')
def logout():
    session.clear()  # Verwijdert alle gegevens uit de sessie
    return redirect(url_for('login'))

# Helpers
def get_logged_in_teacher():
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        return None
    return Teacher.query.get(teacher_id)


if __name__ == '__main__':
    # with app.app_context():
        # import os
        # print("DB pad:", os.path.abspath("data/database.db"))
        # db.create_all()
    app.run(debug=True)