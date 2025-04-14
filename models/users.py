from . import db




# Student Model
class Student(db.Model):
    __tablename__ = 'student'

    st_id = db.Column(db.Integer, primary_key=True)
    st_name = db.Column(db.String(20), nullable=False)
    st_email = db.Column(db.String(50), nullable=False, unique=True)
    st_dob = db.Column(db.Date, nullable=False)
    st_phone = db.Column(db.String(20))
    st_current_inst = db.Column(db.String(30), nullable=False)
    st_password = db.Column(db.String(255), nullable=False)
    st_date_created = db.Column(db.DateTime, nullable=False)

    quiz_histories = db.relationship('QuizHistory', backref='student', lazy=True)

# Teacher Model
class Teacher(db.Model):
    __tablename__ = 'teacher'

    ta_id = db.Column(db.Integer, primary_key=True)
    ta_name = db.Column(db.String(20), nullable=False)
    ta_email = db.Column(db.String(50), nullable=False, unique=True)
    ta_dob = db.Column(db.Date, nullable=False)
    ta_phone = db.Column(db.String(20))
    ta_init = db.Column(db.String(15), nullable=False, unique=True)
    ta_password = db.Column(db.String(255), nullable=False)
    ta_date_created = db.Column(db.DateTime, nullable=False)

    quizzes = db.relationship('Quiz', backref='teacher', lazy=True)


