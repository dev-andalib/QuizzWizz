import datetime
from flask import Blueprint, abort, jsonify,  redirect, render_template, session, request
from sqlalchemy import func
from extra import apology, calculate_total, create_options, decode_options, required_roles
from .auth import send_error, check_email, check_password_hash, generate_password_hash
from models.quiz import Quiz,  QuizHistory, Subject, Question
from models.users import Student, Teacher
from app import db

ta_bp =  Blueprint('ta_bp', __name__)


def calculateAge(year, month, day):
    today = datetime.date.today()
    age = today.year - year - ((today.month, today.day) < (month, day))
    return age


@ta_bp.route("/teacher")
@required_roles("TA")
def red_ta():
    user_id = session.get("user_id")
    if not user_id or not user_id.startswith("TA"):
        return redirect("/logout")

    ta_id = int(user_id[2:])
    teacher = Teacher.query.filter_by(ta_id=ta_id).first()

    if not teacher:
        return redirect("/logout")

    teacher_age = calculateAge(teacher.ta_dob.year, teacher.ta_dob.month, teacher.ta_dob.day)
    teacher.age = teacher_age


    info = db.session.query(
        db.func.count(Quiz.qid).label('created'),
        db.func.sum(QuizHistory.student_id.isnot(None)).label('engaged'),
        db.func.count(db.distinct(QuizHistory.student_id)).label('users')
    ).join(QuizHistory, Quiz.qid == QuizHistory.quiz_id, isouter=True).filter(
        Quiz.set_by == ta_id
    ).first()

    return render_template("home.html", data=teacher, info=info)
 

@ta_bp.route("/teacher/feedbacks")
@required_roles("TA")
def ta_feedbacks():
    set_by = int(session.get("user_id")[2:])
    rows = db.session.query(
        Quiz.qid,
        Quiz.title,
        Quiz.no_of_q,
        Quiz.total_mark,
        Quiz.expired,
        Subject.sname,
        db.func.count(QuizHistory.student_id).label("count"),
        db.func.max(QuizHistory.obtained_marks).label("max_mark")
    ).join(Subject, Quiz.belongs_to == Subject.sid)\
     .outerjoin(QuizHistory, Quiz.qid == QuizHistory.quiz_id)\
     .filter(Quiz.set_by == set_by)\
     .group_by(Quiz.qid, Quiz.title, Quiz.no_of_q, Quiz.total_mark, Quiz.expired, Subject.sname)\
     .order_by(Quiz.qid.desc()).all()
    
    return render_template("show_ta_feedback.html", data=rows)



@ta_bp.route("/teacher/feedbacks/<var>")
@required_roles("TA")
def ta_feedbacks_details(var):
    if not var or not var.isnumeric():
        return redirect("/teacher/feedbacks")

    quiz_idx = int(var)
    set_by = int(session.get("user_id")[2:])

    quiz_exists = db.session.query(Quiz.qid).filter_by(qid=quiz_idx, set_by=set_by).first()
    if not quiz_exists:
        return apology("Not your quiz")

    rows = db.session.query(
        Student.name.label("st_name"),
        Student.current_institute.label("st_current_inst"),
        QuizHistory.obtained_marks,
        QuizHistory.feedback,
        QuizHistory.quiz_date,
        Quiz.total_mark
    ).join(Quiz, Quiz.qid == QuizHistory.quiz_id)\
     .join(Student, Student.sid == QuizHistory.student_id)\
     .filter(Quiz.qid == quiz_idx, Quiz.set_by == set_by).all()

    if not rows:
        return apology("Wrong quiz code!")

    return render_template("show_ta_feedback_detail.html", data=rows)


@ta_bp.route('/teacher/profile', methods=['GET', 'POST'])
@required_roles("TA")
def edit_profile_ta():
    ta_id = int(session.get("user_id")[2:])
    if request.method == "POST":
        username = request.form.get("name")
        email = request.form.get("email")
        dob = request.form.get("dob")
        phone = request.form.get("phone")

        if not username:
            return send_error("Must provide name!")
        elif len(username.strip()) < 4 or len(username.strip()) > 18:
            return send_error("Name must be between 4 and 18 of length")
        if not dob:
            return send_error("Must provide date of birth..!")
        elif not email:
            return send_error("Must provide email..!")
        elif not check_email(email.strip()):
            return send_error("Invalid Email")

        teacher = db.session.query(Teacher).filter_by(ta_id=ta_id).first()
        if teacher.ta_email == email.strip():
            teacher.ta_name = username.strip().title()
            teacher.ta_dob = dob
            teacher.ta_phone = phone
            db.session.commit()
            return send_error("Updated..!")
        else:
            existing = db.session.query(Teacher).filter_by(ta_email=email.strip()).first()
            if existing:
                return send_error("Another account with this email already exists..!")
            teacher.ta_name = username.strip().title()
            teacher.ta_email = email.strip()
            teacher.ta_dob = dob
            teacher.ta_phone = phone
            db.session.commit()
            return send_error("Updated..!")
    else:
        teacher = db.session.query(Teacher).filter_by(ta_id=ta_id).first()
        return render_template("edit_profile.html", data=teacher, role="TA")








@ta_bp.route('/teacher/password', methods=['GET', 'POST'])
@required_roles("TA")
def change_pass_ta():
    ta_id = int(session.get("user_id")[2:])  # e.g., "TA123" → 123

    if request.method == "POST":
        old = request.form.get("oldpassword")
        password = request.form.get("password")
        confirm = request.form.get("password2")

        # Basic validations
        if not old:
            return jsonify({"error": "Must provide old password..!"})
        elif not password:
            return jsonify({"error": "Must provide new password..!"})
        elif not confirm:
            return jsonify({"error": "Must confirm new password"})
        elif len(password) < 8 or len(password) > 20:
            return jsonify({"error": "Invalid Password. Length must be 8-20 characters."})

        # Get TA from database
        ta = Teacher.query.filter_by(ta_id=ta_id).first()
        if not ta or not check_password_hash(ta.ta_password, old):
            return jsonify({"error": "Wrong old password"})

        if confirm != password:
            return jsonify({"error": "Passwords don't match..!"})

        if check_password_hash(ta.ta_password, password):
            return jsonify({"error": "New password is the same as the old one. No changes made."})

        # Update password
        ta.ta_password = generate_password_hash(password)
        db.session.commit()

        return jsonify({"error": "Updated..!"})

    return render_template("change_pass.html", role="TA")






@ta_bp.route("/teacher/quiz", methods=["GET", "POST"])
@required_roles("TA")
def ta_qz_show():
    user_id = session.get("user_id")
    if not user_id or len(user_id) < 3:
        return redirect("/login")  

    set_by = int(user_id[2:])  

    
    quizzes = db.session.query(Quiz.qid, Quiz.title, Quiz.no_of_q, Quiz.total_mark, 
                               Quiz.expired, Quiz.date_created, Subject.sname).\
                join(Subject).\
                filter(Quiz.set_by == set_by).\
                order_by(Quiz.qid.desc()).\
                all()

    return render_template("show_ta_dashboard.html", data=quizzes)



@ta_bp.route("/teacher/quiz/delete", methods=["POST"])
@required_roles("TA")
def ta_qz_del():
    if request.method == "POST":
        idx = request.form.get("idx")
        if not idx:
            return jsonify({"error": "Nice try"}), 400
        
        idx = int(idx)
        set_by = session.get("user_id")[2:]

        quiz = db.session.query(Quiz).filter(Quiz.qid == idx, Quiz.set_by == set_by).first()
        
        if not quiz:
            return jsonify({"error": "You're not the owner. Can't delete!"}), 403
        
        db.session.delete(quiz)
        db.session.commit()
        
        return jsonify({"message": "Deleted!"}), 200



@ta_bp.route("/quiz/geturl", methods=["GET", "POST"])
@required_roles("TA")
def ta_qz_geturl():
    if request.method == "POST":
        idx = request.form.get("idx")
        return send_error(f"/student/quiz/{idx}")



@ta_bp.route("/quiz/<int:quiz_idx>")
@required_roles("TA")
def ta_qz_detail_show(quiz_idx):
    quiz = Quiz.query.get(quiz_idx)
    if not quiz:
        return apology("Wrong quiz code!")

    questions = Question.query.filter_by(belongs_to=quiz.qid).order_by(Question.position).all()
    for question in questions:
        if question.options:
            question.options = decode_options(question.options)

    count = QuizHistory.query.filter_by(quiz_id=quiz.qid).count()

    return render_template("see_quiz_solved_ta.html", data=quiz, ques=questions, count={"st": count})






@ta_bp.route("/quiz/expire", methods=["POST"])
@required_roles("TA")
def ta_qz_expire():
    idx = request.form.get("idx")
    if not idx:
        return send_error("Nice try")

    quiz = Quiz.query.filter_by(qid=int(idx), set_by=int(session["user_id"][2:])).first()
    if not quiz:
        return send_error("You're not the owner. Can't Expire.!")

    quiz.expired = 1
    db.session.commit()
    return send_error("Updated!")









@ta_bp.route("/quiz/create", methods=["GET", "POST"])
@required_roles("TA")
def ta_qz():
    if request.method == "POST":
        title = request.form.get("quiz_title")
        description = request.form.get("quiz_descrip")
        subject_id = request.form.get("subject")
        duration = request.form.get("duration")

        if not title:
            return send_error("Invalid Title")
        if not subject_id:
            return send_error("Choose a subject")
        if not duration or not duration.isnumeric() or int(duration) > 600:
            return send_error("Invalid Duration")

        count = int(request.form.get("count"))
        if count < 4:
            return send_error("Please add at least 3 questions")
        if count > 30:
            return send_error("Can't add more than 30 questions")

        form_data = [request.form.getlist(f"q{i}") for i in range(1, count)]
        total_mark = calculate_total(form_data)

        quiz = Quiz(
            title=title.strip(),
            description=description,
            duration=int(duration),
            no_of_q=count - 1,
            belongs_to=int(subject_id),
            set_by=int(session["user_id"][2:]),
            highest_mark=0,
            total_mark=total_mark,
            expired=0,
            date_created=datetime.now()
        )
        db.session.add(quiz)
        db.session.commit()

        for idx, data in enumerate(form_data):
            if len(data) == 7:  # MCQ
                q = Question(
                    belongs_to=quiz.qid,
                    text=data[0].strip(),
                    marks=int(data[-1]),
                    answer=data[-2].lower(),
                    options=create_options(data[1:5]),
                    position=idx + 1,
                    question_type="mcq"
                )
            elif len(data) == 3:  # Written
                q = Question(
                    belongs_to=quiz.qid,
                    text=data[0].strip(),
                    marks=int(data[-1]),
                    answer=data[-2].lower(),
                    options=None,
                    position=idx + 1,
                    question_type="wrt"
                )
            db.session.add(q)

        db.session.commit()
        return send_error("Created..!")
    else:
        subjects = Subject.query.all()
        return render_template("quiz_set.html", rows=subjects)











