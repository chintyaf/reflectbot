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

