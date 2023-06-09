from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from flask_sslify import SSLify

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
from .models import User
def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'secret-key-do-not-reveal'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurantmenu.db'
    
    db.init_app(app)

    login_manager = LoginManager()  # Create an instance of LoginManager
    login_manager.login_view = 'auth.login'  # Set the login view function
    login_manager.init_app(app)  # Initialise LoginManager with the Flask application


    @login_manager.user_loader
    def load_user(userid):
        return User.query.get(int(userid))  # Load user from the database based on user ID


    sslify = SSLify(app) # Enable HTTPS redirection

    # blueprint for auth routes in our app
    from .json import json as json_blueprint
    app.register_blueprint(json_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
