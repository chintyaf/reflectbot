from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "secret-key"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reflectbot.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .views import views
    from .auth import auth
    from .chat_session import chat_session
    from .chat_message import chat_message
    from .routes.api import api

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(chat_session, url_prefix='/chat')
    app.register_blueprint(chat_message, url_prefix='/chat')
    app.register_blueprint(api, url_prefix='/api')

    from .models import User, ChatMessages, ChatSessions

    create_database(app)

    login_manager = LoginManager() 
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id) :
        return User.query.get(int(id))

    return app

def create_database(app):
    with app.app_context():
        db.create_all()
    print("Database tables created!")
