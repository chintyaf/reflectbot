from . import db 
from flask_login import UserMixin
from sqlalchemy.sql import func

class ChatSessions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    started_at = db.Column(db.DateTime(timezone=True), default=func.now())
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(50), default='active')
    chat_messages = db.relationship('ChatMessages')
    analysis = db.relationship('SessionAnalysis', backref='session', uselist=False, cascade='all, delete-orphan')

class ChatMessages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'))
    sender  = db.Column(db.String(150))
    content = db.Column(db.String(10000))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=func.now())
    journal_chat = db.relationship('ChatSessions')


class SessionAnalysis(db.Model):   
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), unique=True)
    
    # Main Prediction
    attachment_style = db.Column(db.String(50))  # secure, anxious, avoidant
    confidence = db.Column(db.Float)
    probabilities = db.Column(db.Text)  
    
    phrase_analysis = db.Column(db.Text)  
    emotion_analysis = db.Column(db.Text) 
    bert_features = db.Column(db.Text)  
    text_statistics = db.Column(db.Text) 
    timeline_data = db.Column(db.Text)  
    ai_insights = db.Column(db.Text)  
    rule_scores = db.Column(db.Text) 
    
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())