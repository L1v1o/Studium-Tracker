# models.py - Datenbankmodelle für Lern-Tracking App

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Module(db.Model):
    """
    Modul-Tabelle: Speichert Studienfächer mit Zielstunden und Prüfungsdatum
    """
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_hours = db.Column(db.Float, nullable=False)
    exam_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehung zu Sessions (CASCADE: Sessions werden gelöscht wenn Modul gelöscht wird)
    sessions = db.relationship('LearningSession', backref='module', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_sessions=False):
        """Konvertiert Modul zu Dictionary für JSON-Response"""
        data = {
            'id': self.id,
            'name': self.name,
            'target_hours': self.target_hours,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'created_at': self.created_at.isoformat(),
            'actual_hours': self.get_actual_hours(),
            'progress_percentage': self.get_progress_percentage()
        }
        
        if include_sessions:
            data['sessions'] = [session.to_dict() for session in self.sessions]
        
        return data
    
    def get_actual_hours(self):
        """Berechnet die tatsächlich gelernten Stunden für dieses Modul"""
        total = sum(session.duration for session in self.sessions)
        return round(total, 2)
    
    def get_progress_percentage(self):
        """Berechnet Fortschritt in Prozent (Ist/Soll * 100)"""
        if self.target_hours == 0:
            return 0
        return round((self.get_actual_hours() / self.target_hours) * 100, 1)
    
    def __repr__(self):
        return f'<Module {self.name}>'


class LearningSession(db.Model):
    """
    Lern-Session Tabelle: Speichert einzelne Lerneinheiten
    """
    __tablename__ = 'learning_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    duration = db.Column(db.Float, nullable=False)  # in Stunden
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Konvertiert Session zu Dictionary für JSON-Response"""
        return {
            'id': self.id,
            'module_id': self.module_id,
            'module_name': self.module.name if self.module else None,
            'duration': self.duration,
            'date': self.date.isoformat(),
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<LearningSession {self.id} - {self.duration}h>'


class AIRecommendation(db.Model):
    """
    KI-Empfehlungs Tabelle: Speichert generierte Lernpläne von Gemini API
    """
    __tablename__ = 'ai_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    recommendation_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Konvertiert Empfehlung zu Dictionary für JSON-Response"""
        return {
            'id': self.id,
            'recommendation_text': self.recommendation_text,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<AIRecommendation {self.id}>'
