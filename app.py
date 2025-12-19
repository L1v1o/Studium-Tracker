# app.py - Haupt-Flask-Anwendung mit allen API-Routes

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta, date
from sqlalchemy import func
from dotenv import load_dotenv
import logging
import os
import google.generativeai as genai

from models import db, Module, LearningSession, AIRecommendation

# .env Datei laden
load_dotenv()

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Flask-App erstellen und konfigurieren"""
    app = Flask(__name__, static_folder='static', static_url_path='')
    
    # Flask Basis-Konfiguration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DEBUG'] = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Datenbank-Konfiguration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///studium_tracking.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Gemini API Konfiguration
    app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', '')
    app.config['GEMINI_MODEL'] = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
    app.config['GEMINI_TEMPERATURE'] = float(os.getenv('GEMINI_TEMPERATURE', '0.7'))
    app.config['GEMINI_MAX_TOKENS'] = int(os.getenv('GEMINI_MAX_TOKENS', '2048'))
    
    # JSON Konfiguration
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # CORS aktivieren
    CORS(app)
    
    # Datenbank initialisieren
    db.init_app(app)
    
    # Gemini API konfigurieren
    if app.config['GEMINI_API_KEY'] and app.config['GEMINI_API_KEY']:
        try:
            genai.configure(api_key=app.config['GEMINI_API_KEY'])
            logger.info("Gemini API erfolgreich konfiguriert")
        except Exception as e:
            logger.error(f"Fehler bei Gemini API Konfiguration: {e}")
    else:
        logger.warning("GEMINI_API_KEY nicht gesetzt - KI-Funktionen deaktiviert")
    
    # Datenbank-Tabellen erstellen
    with app.app_context():
        db.create_all()
        logger.info("Datenbank-Tabellen erstellt/überprüft")
    
    return app


app = create_app()

def validate_date(date_string):
    """Validiert Datumsformat YYYY-MM-DD"""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def get_sessions_by_date_range(start_date, end_date):
    """Holt alle Sessions innerhalb eines Datumsbereichs"""
    return LearningSession.query.filter(
        LearningSession.date >= start_date,
        LearningSession.date <= end_date
    ).all()


def calculate_total_hours(sessions):
    """Berechnet Gesamtstunden aus Sessions"""
    return round(sum(session.duration for session in sessions), 2)

@app.route('/api/modules', methods=['POST'])
def create_module():
    """
    POST /api/modules - Erstellt ein neues Modul
    Body: { "name": str, "target_hours": float, "exam_date": str (YYYY-MM-DD) }
    """
    try:
        data = request.get_json()
        
        # Validierung
        if not data or 'name' not in data or 'target_hours' not in data:
            return jsonify({'error': 'Name und target_hours sind erforderlich'}), 400
        
        if data['target_hours'] < 0:
            return jsonify({'error': 'target_hours darf nicht negativ sein'}), 400
        
        # Exam Date validieren (optional)
        exam_date = None
        if 'exam_date' in data and data['exam_date']:
            exam_date = validate_date(data['exam_date'])
            if exam_date is None:
                return jsonify({'error': 'Ungültiges Datumsformat. Nutze YYYY-MM-DD'}), 400
        
        # Modul erstellen
        module = Module(
            name=data['name'],
            target_hours=float(data['target_hours']),
            exam_date=exam_date
        )
        
        db.session.add(module)
        db.session.commit()
        
        logger.info(f"Neues Modul erstellt: {module.name} (ID: {module.id})")
        return jsonify(module.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Moduls: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/modules', methods=['GET'])
def get_modules():
    """
    GET /api/modules - Gibt alle Module mit Fortschrittsberechnung zurück
    """
    try:
        modules = Module.query.all()
        return jsonify([module.to_dict() for module in modules]), 200
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Module: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/modules/<int:module_id>', methods=['GET'])
def get_module(module_id):
    """
    GET /api/modules/<id> - Gibt Modul-Details inkl. aller Sessions zurück
    """
    try:
        module = Module.query.get_or_404(module_id)
        return jsonify(module.to_dict(include_sessions=True)), 200
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Moduls {module_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/modules/<int:module_id>', methods=['DELETE'])
def delete_module(module_id):
    """
    DELETE /api/modules/<id> - Löscht Modul und alle zugehörigen Sessions (CASCADE)
    """
    try:
        module = Module.query.get_or_404(module_id)
        module_name = module.name
        
        db.session.delete(module)
        db.session.commit()
        
        logger.info(f"Modul gelöscht: {module_name} (ID: {module_id})")
        return jsonify({'message': f'Modul "{module_name}" erfolgreich gelöscht'}), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Moduls {module_id}: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """
    POST /api/sessions - Erstellt eine neue Lern-Session
    Body: { "module_id": int, "duration": float, "date": str (YYYY-MM-DD), "notes": str }
    """
    try:
        data = request.get_json()
        
        # Validierung
        required_fields = ['module_id', 'duration', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} ist erforderlich'}), 400
        
        if data['duration'] <= 0:
            return jsonify({'error': 'duration muss größer als 0 sein'}), 400
        
        # Modul existiert?
        module = Module.query.get(data['module_id'])
        if not module:
            return jsonify({'error': 'Modul nicht gefunden'}), 404
        
        # Datum validieren
        session_date = validate_date(data['date'])
        if session_date is None:
            return jsonify({'error': 'Ungültiges Datumsformat. Nutze YYYY-MM-DD'}), 400
        
        # Session erstellen
        session = LearningSession(
            module_id=data['module_id'],
            duration=float(data['duration']),
            date=session_date,
            notes=data.get('notes', '')
        )
        
        db.session.add(session)
        db.session.commit()
        
        logger.info(f"Neue Session erstellt: {session.duration}h für Modul {module.name}")
        return jsonify(session.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Session: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """
    GET /api/sessions - Gibt alle Sessions chronologisch sortiert zurück
    Query-Parameter: ?limit=20 (optional)
    """
    try:
        limit = request.args.get('limit', type=int)
        
        query = LearningSession.query.order_by(LearningSession.date.desc())
        
        if limit:
            query = query.limit(limit)
        
        sessions = query.all()
        return jsonify([session.to_dict() for session in sessions]), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Sessions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    DELETE /api/sessions/<id> - Löscht eine Session
    """
    try:
        session = LearningSession.query.get_or_404(session_id)
        
        db.session.delete(session)
        db.session.commit()
        
        logger.info(f"Session gelöscht: ID {session_id}")
        return jsonify({'message': 'Session erfolgreich gelöscht'}), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Session {session_id}: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def create_recommendation():
    """
    POST /api/recommend - Ruft Gemini API auf und speichert Empfehlung
    """
    try:
        # Prüfe ob API konfiguriert ist
        if not app.config['GEMINI_API_KEY'] or app.config['GEMINI_API_KEY'] == 'your-api-key-here':
            return jsonify({
                'error': 'Gemini API nicht konfiguriert',
                'message': 'Bitte GEMINI_API_KEY Umgebungsvariable setzen'
            }), 503

        # Hole alle Module mit ihren Daten
        modules = Module.query.all()

        if not modules:
            return jsonify({
                'error': 'Keine Module vorhanden',
                'message': 'Bitte erstelle zuerst Module, bevor du eine Empfehlung anforderst'
            }), 400

        # Erstelle Prompt für Gemini
        prompt = "Ich lerne für folgende Module:\n\n"

        for module in modules:
            actual_hours = module.get_actual_hours()
            remaining_hours = max(0, module.target_hours - actual_hours)
            exam_info = f" (Prüfung am {module.exam_date.strftime('%d.%m.%Y')})" if module.exam_date else ""

            prompt += f"- {module.name}: Ziel {module.target_hours}h, bereits gelernt {actual_hours}h, "
            prompt += f"noch {remaining_hours}h offen{exam_info}\n"

        prompt += """
        Du bist ein intelligenter Lernplan-Generator.
        Erstelle auf Basis der folgenden Eingaben einen detaillierten, realistischen Lernplan für die nächsten 2 Wochen.

        **Ziel:**
        Erstelle einen Lernplan, der die Vorbereitung optimal auf die kommenden Prüfungen verteilt.
        Gib für jeden Tag folgendes an:
        - Datum
        - zu lernende Module
        - empfohlene Lernzeit in Stunden pro Modul
        - ggf. kurze Lernziele oder Schwerpunkt-Themen

        **Anforderungen an die Ausgabe:**
        - Zeitraum: die nächsten 14 Tage (beginnend ab heute oder ab angegebenem Startdatum)
        - Ausgabe im klaren, tabellarischen oder Listenformat
        - Achte auf eine realistische Verteilung der Lernzeit (keine 10 Stunden am Stück)
        - Berücksichtige Ruhetage oder kürzere Lerneinheiten an Wochenenden

        **Format der Antwort:**
        Tag (Datum):
        - Modul: X Stunden – Thema/Fokus: ...
        """

        logger.info(f"Sende Anfrage an Gemini API (Modell: {app.config['GEMINI_MODEL']})...")
        
        # Gemini API aufrufen mit konfigurierbaren Parametern
        model = genai.GenerativeModel(app.config['GEMINI_MODEL'])
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': app.config['GEMINI_TEMPERATURE'],
                'max_output_tokens': app.config['GEMINI_MAX_TOKENS']
            }
        )
        
        if not response or not response.text:
            raise Exception("Keine Antwort von Gemini API erhalten")        # Empfehlung speichern
        recommendation = AIRecommendation(
            recommendation_text=response.text
        )

        db.session.add(recommendation)
        db.session.commit()

        logger.info(f"Neue KI-Empfehlung erstellt (ID: {recommendation.id})")
        return jsonify(recommendation.to_dict()), 201

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Empfehlung: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'Fehler bei der KI-Generierung',
            'message': str(e)
        }), 500


@app.route('/api/recommend', methods=['GET'])
def get_recommendation():
    """
    GET /api/recommend - Gibt die letzte Empfehlung zurück
    """
    try:
        recommendation = AIRecommendation.query.order_by(
            AIRecommendation.created_at.desc()
        ).first()
        
        if not recommendation:
            return jsonify({'message': 'Noch keine Empfehlung vorhanden'}), 404
        
        return jsonify(recommendation.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Empfehlung: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """
    GET /api/dashboard - Übersicht mit Statistiken
    Returns: Gesamtstunden heute/Woche/Monat, alle Module, letzte Empfehlung
    """
    try:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Sessions für verschiedene Zeiträume
        today_sessions = get_sessions_by_date_range(today, today)
        week_sessions = get_sessions_by_date_range(week_start, today)
        month_sessions = get_sessions_by_date_range(month_start, today)
        
        # Stunden berechnen
        hours_today = calculate_total_hours(today_sessions)
        hours_week = calculate_total_hours(week_sessions)
        hours_month = calculate_total_hours(month_sessions)
        
        # Alle Module mit Fortschritt
        modules = Module.query.all()
        
        # Letzte Empfehlung
        last_recommendation = AIRecommendation.query.order_by(
            AIRecommendation.created_at.desc()
        ).first()
        
        dashboard_data = {
            'statistics': {
                'hours_today': hours_today,
                'hours_week': hours_week,
                'hours_month': hours_month,
                'sessions_today': len(today_sessions),
                'sessions_week': len(week_sessions),
                'total_modules': len(modules)
            },
            'modules': [module.to_dict() for module in modules],
            'last_recommendation': last_recommendation.to_dict() if last_recommendation else None
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Dashboards: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Serve Frontend HTML"""
    return send_from_directory('static', 'index.html')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Ressource nicht gefunden'}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Interner Serverfehler'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
