from flask import Blueprint, render_template
from flask_login import login_required, current_user
views = Blueprint('views', __name__)
from .models import ChatSessions


@views.route('/', methods=['GET'])
@login_required
def home():
    chat_sessions = (
        ChatSessions.query
        .filter_by(user_id=current_user.id)
        .order_by(ChatSessions.started_at.desc())
        .all()
    )

    return render_template("index.html", chat_session=chat_sessions)

