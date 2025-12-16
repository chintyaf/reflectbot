from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .models import ChatSessions, ChatMessages
from . import db

chat_message = Blueprint('chat_message', __name__)

@chat_message.route('/<int:session_id>/send', methods=['POST'])
@login_required
def send_message(session_id):
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    content = request.form.get('message')

    msg = ChatMessages(
        session_id=session.id,
        sender=current_user.name,
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
