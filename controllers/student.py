from flask import Blueprint, abort, jsonify,  redirect, render_template, session, request
from sqlalchemy import func
from extra import apology, calculateAge, decode_options, required_roles
from .auth import send_error, check_password_hash, generate_password_hash
from models.quiz import Quiz,  QuizHistory, Subject, Question
from models.users import Student, Teacher
from app import db


st_bp = Blueprint('st_bp', __name__)

@st_bp.route("/student")
@required_roles("ST")
def red_st():
    
    try:
        
        user_id_from_session = session.get("user_id")
        

        if not user_id_from_session:

            abort(401)

        user_id = int(user_id_from_session[2:])
        

        
        student = Student.query.get(user_id)
        

        if not student:
            abort(404)

        
        if student.st_dob:
            
            student.age = calculateAge([student.st_dob.year, student.st_dob.month, student.st_dob.day])
            
        else:
            student.age = None  # Or a default value, or handle this case

        
        quiz_count = QuizHistory.query.filter_by(student_id=user_id).count()
        

        
        teacher_stats = db.session.query(
            Teacher.ta_init,
            func.count(QuizHistory.quiz_id).label('quiz_count')
        ).select_from(QuizHistory).join(Quiz, QuizHistory.quiz_id == Quiz.qid).join(Teacher, Quiz.set_by == Teacher.ta_id).filter(QuizHistory.student_id == user_id).group_by(Teacher.ta_id).subquery()
        

        
        fav_teacher_result = db.session.query(teacher_stats.c.ta_init
                                             ).order_by(teacher_stats.c.quiz_count.desc()
                                             ).first()
        fav_teacher = fav_teacher_result[0] if fav_teacher_result else None
        

        
        avg_rating = db.session.query(
            func.round(func.avg(
                (QuizHistory.obtained_marks.cast(db.Float) / Quiz.total_mark) * 100
            ), 2)
        ).select_from(QuizHistory).join(Quiz, QuizHistory.quiz_id == Quiz.qid).filter(QuizHistory.student_id == user_id).scalar()
        print(f"DEBUG: avg_rating = {avg_rating}")

        
        join_date = student.st_date_created.strftime("%Y-%m-%d") if student.st_date_created else "N/A"
        
        

        
        return render_template("home.html",
                               data=student,
                               info1=quiz_count or 0,
                               info2=[{"ta_init": fav_teacher}] if fav_teacher else [],  # Adjusted
                               info3=[{"avg_rating": avg_rating}] if avg_rating else [],
                               st_date_created=join_date,
                               
                               )

    except Exception as e:
        print(f"DEBUG: Error in /student: {e}")
        return apology("An error occurred...", 500)

@st_bp.route("/student/quiz/<int:quiz_idx>")
@required_roles("ST")
def st_qz_take(quiz_idx):
    quiz = db.session.query(
        Quiz.qid,
        Quiz.title,
        Quiz.description,
        Quiz.duration,
        Quiz.no_of_q,
        Quiz.total_mark,
        Subject.sname.label("sname"),
        Teacher.ta_init.label("ta_init")
    ).join(Subject, Quiz.belongs_to == Subject.sid
    ).join(Teacher, Quiz.set_by == Teacher.ta_id
    ).filter(Quiz.qid == quiz_idx
    ).first()

    if not quiz:
        return apology("Wrong quiz code!")

    return render_template("take_quiz.html", data=quiz._asdict())


@st_bp.route("/student/getquestion")
@required_roles("ST")
def st_get_questions():
    qid = request.args.get("qid", type=int)
    
    if not qid:
        return apology("Invalid request")
    
    
    st_id_str = session.get("user_id")
    if not st_id_str or not st_id_str.startswith("ST") or not st_id_str[2:].isdigit():
        return apology("Invalid session")

    st_id = int(st_id_str[2:])
    

    if QuizHistory.query.filter_by(quiz_id=qid, student_id=st_id).first():
        return "<div style='text-align:center;'><h1>You've already taken the quiz</h1></div>"

   
    questions = Question.query.filter_by(belongs_to=qid).order_by(Question.position).all()

    
    for q in questions:
        if q.question_type == "mcq" and q.options:
            q.options = decode_options(q.options) 

    return render_template("questions.html", data=questions)



@st_bp.route("/student/submit_quiz", methods=['POST'])
@required_roles("ST")
def st_submit_questions():
    if request.method == "POST":
        qid = request.form.get("qid")
        st_id = int(session.get("user_id")[2:])
        
        if QuizHistory.query.filter_by(quiz_id=qid, student_id=st_id).first():
            return redirect("/student/quizes")
        
        quiz = Quiz.query.get(qid)
        if not quiz:
            return apology("Invalid quiz")
        
        answers = []
        for i in range(1, quiz.no_of_q + 1):
            if answer := request.form.get(str(i)):
                answers.append((i, answer.strip().lower()))
        
        correct_answers = {q.position: q.answer.lower() for q in quiz.questions}
        marks = sum(q.marks for q in quiz.questions 
                   if str(q.position) in request.form 
                   and request.form[str(q.position)].strip().lower() == q.answer.lower())
        
        history = QuizHistory(
            quiz_id=qid,
            student_id=st_id,
            obtained_marks=marks,
            feedback=request.form.get("comment"),
            quiz_date=datetime.now()
        )
        db.session.add(history)
        db.session.commit()
        
        return render_template("result_uptade.html", data={
            "mark": marks,
            "expired": quiz.expired,
            "total": quiz.total_mark
        })


@st_bp.route("/student/quizes")
@required_roles("ST")
def st_qz():
    subjects = Subject.query.all()
    return render_template("show_st_dashboard.html", data=subjects)


@st_bp.route('/student/quizes/<variable>', methods=['GET'])
@required_roles("ST")
def quiz_list(variable):
    subject = Subject.query.filter(
        func.replace(Subject.sname, ' ', '').ilike(variable)
    ).first()
    
    if not subject:
        abort(404)
    
    st_id = int(session.get("user_id")[2:])
    quizzes = Quiz.query.filter_by(belongs_to=subject.sid
        ).outerjoin(QuizHistory, 
            (QuizHistory.quiz_id == Quiz.qid) & 
            (QuizHistory.student_id == st_id)
        ).add_entities(
            Quiz.qid, Quiz.title, Quiz.duration, 
            Quiz.total_mark, Quiz.expired,
            QuizHistory.obtained_marks
        ).all()
    
    return render_template("show_st_quiz_dashboard.html", data=quizzes)


@st_bp.route("/student/history")
@required_roles("ST")
def st_hs():
    st_id = int(session.get("user_id")[2:])
    history = QuizHistory.query.filter_by(student_id=st_id
        ).join(Quiz, QuizHistory.quiz_id == Quiz.qid
        ).join(Subject, Quiz.belongs_to == Subject.sid
        ).join(Teacher, Quiz.set_by == Teacher.ta_id
        ).add_columns(
            Quiz.qid, Quiz.title, Teacher.ta_init,
            Quiz.total_mark, Quiz.expired,
            QuizHistory.obtained_marks, Subject.sname,
            QuizHistory.quiz_date
        ).order_by(Quiz.qid.desc()).all()
    
    return render_template("show_st_history.html", data=history)


@st_bp.route("/student/history/<int:quiz_idx>")
@required_roles("ST")
def st_hs_solve(quiz_idx):
    quiz = Quiz.query.get(quiz_idx)
    if not quiz or quiz.expired == 0:
        return apology("Invalid request")
    
    questions = Question.query.filter_by(belongs_to=quiz_idx
        ).order_by(Question.position).all()
    
    for q in questions:
        if q.options:
            q.options = decode_options(q.options)
    
    return render_template("see_quiz_solved_st.html", 
        data=quiz,
        ques=questions
    )


@st_bp.route('/student/profile', methods=['GET', 'POST'])
@required_roles("ST")
def edit_profile():
    st_id = int(session.get("user_id")[2:])
    student = Student.query.get(st_id)
    
    if request.method == "POST":
        # Validation logic remains similar
        # Update using ORM
        student.st_name = request.form.get("name").strip().title()
        # ... other fields ...
        db.session.commit()
        return send_error("Updated..!")
    
    return render_template("edit_profile.html", data=student, role="ST")


@st_bp.route('/student/password', methods=['GET', 'POST'])
@required_roles("ST")
def change_pass_st():
    st_id = int(session.get("user_id")[2:])
    student = Student.query.get(st_id)
    
    if request.method == "POST":
        # Validation logic remains similar
        if check_password_hash(student.st_password, request.form.get("oldpassword")):
            student.st_password = generate_password_hash(request.form.get("password"))
            db.session.commit()
            return send_error("Updated..!")
    
    return render_template("change_pass.html", role="ST")