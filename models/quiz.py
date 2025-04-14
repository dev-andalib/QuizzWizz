from app import db



# Subject Model
class Subject(db.Model):
    __tablename__ = 'subject'

    sid = db.Column(db.Integer, primary_key=True)
    sname = db.Column(db.String(15), nullable=False)

    quizzes = db.relationship('Quiz', backref='subject', lazy=True)

# Quiz Model
class Quiz(db.Model):
    __tablename__ = 'quiz'

    qid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(15), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, nullable=False)
    no_of_q = db.Column(db.Integer, nullable=False)
    belongs_to = db.Column(db.Integer, db.ForeignKey('subject.sid', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    set_by = db.Column(db.Integer, db.ForeignKey('teacher.ta_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    highest_mark = db.Column(db.Integer)
    total_mark = db.Column(db.Integer, nullable=False)
    expired = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)

    questions = db.relationship('Question', backref='quiz', lazy=True)
    quiz_histories = db.relationship('QuizHistory', backref='quiz', lazy=True)

# Question Model
class Question(db.Model):
    __tablename__ = 'question'

    quid = db.Column(db.Integer, primary_key=True)
    belongs_to = db.Column(db.Integer, db.ForeignKey('quiz.qid', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    marks = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)
    position = db.Column(db.Integer, nullable=False)
    question_type = db.Column(db.String(45), nullable=False)