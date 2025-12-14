from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
DB_NAME = "reflectbot.db"

def create_app():
    app = Flask(__name__)
    # secure cookies
    app.config['SECRET_KEY'] = "secret-key"
    app.config['SQ:LALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='')
    

    return app
