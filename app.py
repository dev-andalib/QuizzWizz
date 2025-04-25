from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from flask_session import Session
from config import Config
from models import db


from controllers.index import index_bp
from controllers.auth import auth_bp
from controllers.student import st_bp
from controllers.teacher import ta_bp



def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)
    db.init_app(app)
    
    
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.testing = False
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"

    
    Session(app)

    
    with app.app_context():
        from models.users import Student, Teacher
        from models.quiz import Subject, Quiz, QuizHistory, Question
        inspector = inspect(db.engine)
        if not inspector.has_table('student'): 
            db.create_all()
            print("DB newly created")


    app.register_blueprint(index_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(st_bp)
    app.register_blueprint(ta_bp)
    return app
