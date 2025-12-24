from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
chat_session = Blueprint('chat_session', __name__)
from .models import ChatSessions
from . import db



@chat_session.route('/')
@login_required
def create():
    new_chat = ChatSessions(user_id=current_user.id)
    db.session.add(new_chat)
    db.session.commit()

    return redirect(
        url_for('chat_session.detail', session_id=new_chat.id)
    )

@chat_session.route('/<int:session_id>')
@login_required
def detail(session_id) :
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    return render_template(
        "chat/chatbot.html",
        user=current_user,
        session=session
    )

@chat_session.route('/<int:session_id>/delete')
@login_required
def delete(session_id) :
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(session)
    db.session.commit()

    return redirect(url_for('views.home'))