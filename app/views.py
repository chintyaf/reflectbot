from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import ChatSessions
views = Blueprint('views', __name__)


@views.route('/')
@login_required
def home():
    sessions = ChatSessions.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatSessions.started_at.desc()).all()

    return render_template(
        "index.html",
        name="Chintya",
        user=current_user,
        sessions=sessions
    )
