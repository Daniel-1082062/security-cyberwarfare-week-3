import json
from app import app
from db import db
from models import Statement, StatementChoice

# Laad het json bestand in
with app.app_context():
    with open('data/actiontype_statements.json') as f:
        data = json.load(f)

# Check of het statement nummer al in de datbase staat,
        for item in data:
            number = item['statement_number']
            existing = Statement.query.filter_by(statement_number=number).first()
            # Als het statement nummer nog niet in de database staat, wordt er een statement met dit nummer aangemaakt en wordt er via flush automatisch een id aan het statement object toegevoegd.
            if not existing:
                statement = Statement(statement_number=number)
                db.session.add(statement)
                db.session.flush()
                #Voegt voor elke statement choice een object toe
                for choice in item['statement_choices']:
                    statement_choice = StatementChoice(
                        statement_id=statement.statement_id,
                        choice_number=choice['choice_number'],
                        choice_text=choice['choice_text'],
                        choice_result=choice['choice_result'],
                    )
                    db.session.add(statement_choice)

        db.session.commit()
        print(f"{len(data)} stellingen geïmporteerd.")

        s = Statement.query.first()
        print(s.statement_choices)