from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .users import *
from .quiz import *