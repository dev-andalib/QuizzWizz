from random import randint
from datetime import datetime
from flask import  flash,  Blueprint, jsonify,  redirect, render_template, session, request
from werkzeug.security import check_password_hash, generate_password_hash
from extra import check_email, apology
from models import db, Student, Teacher


auth_bp = Blueprint('auth_bp', __name__)



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        if not email:
            flash("Where's the email..?", 'error')
            return render_template("login.html")
        elif not password:
            flash("Where's the password..?", 'error')
            return render_template("login.html")
        elif not role:
            flash("Where's the role..?", 'error')
            return render_template("login.html")
        elif role not in ["student", "teacher"]:
            flash("Invalid role.", 'error')
            return render_template("login.html")

        if role == "student":
            student = Student.query.filter_by(st_email=email.strip()).first()
            if not student or not check_password_hash(student.st_password, password):
                flash("Invalid user or password.", 'error')
                return render_template("login.html")

            session["user_id"] = "ST" + str(student.st_id)

        elif role == "teacher":
            teacher = Teacher.query.filter_by(ta_email=email.strip()).first()
            if not teacher or not check_password_hash(teacher.ta_password, password):
                flash("Invalid user or password.", 'error')
                return render_template("login.html")

            session["user_id"] = "TA" + str(teacher.ta_id)

        flash("Login successful!")
        return redirect("/")

    else:
        if session.get("user_id") is None:
            return render_template("login.html")
        else:
            return redirect("/")

@auth_bp.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

def send_error(message):
    return jsonify(error=message)

@auth_bp.route("/signup_teacher", methods=["GET", "POST"])
def signup_t():
    if request.method == "POST":
        # Get form data
        username = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("password2")
        dob = request.form.get("dob")
        phone = request.form.get("phone")

        # Validation
        if not username:
            return send_error("Must provide name!")
        elif len(username.strip()) < 4 or len(username.strip()) > 18:
            return send_error("Name must be between 4 and 18 characters in length")

        if not dob:
            return send_error("Must provide date of birth..!")

        if not email:
            return send_error("Must provide email..!")

        if not check_email(email.strip()):
            return send_error("Invalid Email")

        if not password:
            return send_error("Must provide password..!")

        if len(password) < 8 or len(password) > 20:
            return send_error("Password must be between 8 and 20 characters.")

        if not confirm or confirm != password:
            return send_error("Passwords don't match..!")

        # Check if email already exists
        teacher = Teacher.query.filter_by(ta_email=email.strip()).first()
        if teacher:
            return send_error("Email already exists..!")

        # Get timestamp for account creation
        date_created = datetime.now().strftime("%d/%m/%y %H:%M:%S")

        # Create new teacher record (without init for now)
        new_teacher = Teacher(
            ta_name=username.strip().capitalize(),
            ta_email=email.strip(),
            ta_dob=dob,
            ta_phone=phone,
            ta_password=generate_password_hash(password),
            ta_date_created=date_created
        )

        db.session.add(new_teacher)
        db.session.commit()  # So that new_teacher.ta_id is generated

        # Now generate a unique init using the generated ta_id
        teacher_init = (
            username[randint(0, len(username) - 1)] +
            username[randint(0, len(username) - 1)] +
            username[randint(0, len(username) - 1)] +
            str(new_teacher.ta_id + 20230)
        ).upper()

        new_teacher.ta_init = teacher_init
        db.session.commit()  # Save updated init

        
        return jsonify(error="Registered..!")

    else:
        if session.get("user_id"):
            return redirect("/")
        return render_template("signup_teacher.html")

def send_error(message):
    return jsonify(error=message)

@auth_bp.route("/signup_student", methods=["GET", "POST"])
def signup_s():
    if request.method == "POST":
        # Get form data
        username = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("password2")
        dob = request.form.get("dob")
        inst = request.form.get("institute")
        phone = request.form.get("phone")

        # Validation
        if not username:
            return send_error("Must provide name!")
        elif len(username.strip()) < 4 or len(username.strip()) > 18:
            return send_error("Name must be between 4 and 18 characters in length")
        
        if not dob:
            return send_error("Must provide date of birth..!")
        
        if not email:
            return send_error("Must provide email..!")
        
        if not check_email(email.strip()):  # Assuming check_email is a custom function for email validation
            return send_error("Invalid Email")
        
        if not inst:
            return send_error("Must provide institute..!")
        
        if not 6 < len(inst) < 30:
            return send_error("Must provide valid institute..!")

        if not password:
            return send_error("Must provide password..!")
        
        if len(password) < 8 or len(password) > 20:
            return send_error("Password must be between 8 and 20 characters.")
        
        if not confirm or confirm != password:
            return send_error("Passwords don't match..!")

        # Check if email already exists
        student = Student.query.filter_by(st_email=email.strip()).first()

        if student:
            return send_error("Email already exists..!")

        # Create the new student record
        date_created = datetime.now().strftime("%d/%m/%y %H:%M:%S")

        # Create the Student instance
        new_student = Student(
    st_name=username.strip().capitalize(),
    st_email=email.strip(),
    st_dob=dob,
    st_phone=phone,
    st_current_inst=inst.strip().capitalize(),
    st_password=generate_password_hash(password),
    st_date_created=date_created
        )

        # Add the new student to the session and commit
        db.session.add(new_student)
        db.session.commit()

        return jsonify(error="Registered..!")

    else:
        # If user is already logged in, redirect to home
        if session.get("user_id"):
            return redirect("/")
        else:
            return render_template("signup_student.html")

@auth_bp.route("/notyours")
def sendrr():
    if session.get("user_id") is None:
        return redirect("/login")

    usr = session["user_id"][:2]
    if usr=="ST":
        return apology("You're not a Teacher")
    elif usr=="TA":
        return apology("You're not a teacher")
    
@auth_bp.route("/choose")
def choose():
    if session.get("user_id") is None:
        return render_template("choose.html")
    else:
        return redirect("/")