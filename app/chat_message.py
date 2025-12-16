from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .models import ChatSessions, ChatMessages
from . import db

chat_message = Blueprint('chat_message', __name__)

@chat_message.route('/<int:session_id>/read')
@login_required
def read_messages(session_id):
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    messages = ChatMessages.query.filter_by(session_id=session.id).order_by(ChatMessages.created_at).all()

    messages_data = [{
        "id": msg.id,
        "sender": msg.sender,
        "content": msg.content,
        "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for msg in messages]

    return jsonify(messages_data)

@chat_message.route('/<int:session_id>/send', methods=['POST'])
@login_required
def send_message(session_id):
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    content = request.form.get('message')
    sender = request.form.get('sender')

    msg = ChatMessages(
        session_id=session.id,
        sender=sender,
        content=content
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({
        "id": msg.id,
        "sender": msg.sender,
        "content": msg.content,
        "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })
