# werkplaats-3-inhaalopdracht-actiontypes
Template voor de WP3 inhaalopdracht "action types"

Deze repository bevat de volgende bestanden:
- De opdrachtomschrijving: [CASUS.md](CASUS)
- Een openapi specificatie voor het ontwerp van de API: [openapi.yaml](openapi.yaml)
- Een lijst met action types: [actiontype_statements.json](actiontype_statements.json)
- Een lijst met initiële studenten: [studenten.json](studenten.json)

Je mag dit document leegmaken en gebruiken voor documentatie van jouw uitwerking. 



# Requirements

Los van Python en Docker zijn een aantal packages benodigd om de applicatie te draaien. Deze kun je vinden in het bestand genaamd 'requirements.txt'

Installeer de packages eenvoudig door de volgende command in te voeren in de terminal.
   ```bash
   pip install -r requirements.txt
   ```

Importeer nu eerst de data door het import_statements.py script te draaien.

```bash
    python import_statements.py
```

Om ook de studenten te importeren, kun je het import_students.py script draaien.
```bash
    python import_students.py
```

Start vervolgens app.py op. De webapp draait nu op http://localhost:5000 ofwel http://127.0.0.1:5000/

```bash
    python app.py
```

# Inloggen als docent

Om in te loggen als docent met adminrechten, kun je de volgende gegevens gebruiken:<br>
<ul>
<li>Gebruikersnaam: admin</li>
<li>Wachtwoord: geheim123</li>
</ul>
Wil je inloggen als docent zonder adminrechten?
<ul>
<li>Gebruikersnaam: noadmin</li>
<li>Wachtwoord: geheim123</li>
</ul>

# Functionaliteiten
Studenten vullen stellingen in.<br>
Na afloop verschijnt het MBTI-profiel. Herhalen is niet mogelijk.<br><br>
Docenten kunnen:
<ul>
<li>Studenten beheren</li>
<li>Teams beheren</li>
<li>Docenten beheren (alleen als admin)</li>
<li>Resultaten bekijken en filteren</li>
<li>Studenten aan teams koppelen</li>
</ul>

Daniël Eijkel - 1082062<br>
Mei 2025
