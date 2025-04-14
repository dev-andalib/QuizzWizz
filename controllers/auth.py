from random import randint
from datetime import datetime
from flask import  flash,  Blueprint,  redirect, render_template, session, request
from werkzeug.security import check_password_hash, generate_password_hash
from extra import check_email, send_error, apology



auth_bp = Blueprint('auth_bp', __name__)



@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if not request.form.get("email"):
            flash("Where's the email..?", 'error')
            return render_template("login.html")

        elif not request.form.get("password"):
            flash("Where's the password..?", 'error')
            return render_template("login.html")

        elif not request.form.get("role"):
            flash("Where's the role..?", 'error')
            return render_template("login.html")

        elif request.form.get("role") not in ["student", "teacher"]:
            flash("Invalid role.", 'error')
            return render_template("login.html")

        role = request.form.get("role")
        if role=="student":
            rows = db.execute("SELECT st_id, st_password FROM student WHERE st_email = ?", (request.form.get("email"),)).fetchall()
            if len(rows) != 1 or not check_password_hash(rows[0]["st_password"], request.form.get("password")):
                flash("Invalid user or password.", 'error')
                return render_template("login.html")
            
            session["user_id"] = "ST" + str(rows[0]["st_id"])

            
        elif role=="teacher":
            rows = db.execute("SELECT ta_id, ta_password FROM teacher WHERE ta_email = ?", (request.form.get("email"),)).fetchall()
            if len(rows) != 1 or not check_password_hash(rows[0]["ta_password"], request.form.get("password")):
                flash("Invalid user or password.", 'error')
                return render_template("login.html")
            
            session["user_id"] = "TA" + str(rows[0]["ta_id"])

        flash("Login successful.!")
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





@auth_bp.route("/signup_teacher", methods=["GET", "POST"])
def signup_t():
    if request.method=="POST":
        username = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("password2")
        dob = request.form.get("dob")
        phone = request.form.get("phone")

        if not username:
            return send_error("Must provide name!")

        elif len(username.strip())<4 or len(username.strip())>18:
            return send_error("Name must be between 4 and 18 of length")
        
        if not dob:
            return send_error("Must provide date of birth..!")

        elif not email:
            return send_error("Must provide email..!")

        elif not check_email(email.strip()):
            return send_error("Invalid Email")
        
        elif not password:
            return send_error("Must provide password..!")
        
        elif len(password)<8 or len(password) >20:
            return send_error("Invalid Password")

        elif not confirm or confirm != password:
            return send_error("Passwords don't match..!")
        
        # Check if user already exists
        rows = db.execute("SELECT ta_id FROM teacher WHERE ta_email = ?", (email.strip(),)).fetchall()
        if len(rows)!=0:
            return send_error("Email already exists..!")
        
        init = (username[randint(0, len(username))] + username[randint(0, len(username))] + username[randint(0, len(username))] + (str(db.execute("SELECT MAX(ta_id) as init From teacher").fetchall()[0]["init"]+20230))).upper()

        date = datetime.now().strftime("%d/%m/%y %H:%M:%S")
        db.execute("INSERT INTO teacher (ta_name, ta_email, ta_dob, ta_phone, ta_init, ta_password, ta_date_created) VALUES(?, ?, ?, ?, ?, ?, ?)", (username.strip().capitalize(), email.strip(), dob, phone, init, generate_password_hash(password), date))
        con.commit()

        return send_error("Registered..!")
        
    else:
        if session.get("user_id") is None:
            return render_template("signup_teacher.html")

        else:
            return redirect("/")


@auth_bp.route("/signup_student", methods=["GET", "POST"])
def signup_s():
    if request.method=="POST":
        # Validate the user data
        username = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("password2")
        dob = request.form.get("dob")
        inst = request.form.get("institute")
        phone = request.form.get("phone")

        if not username:
            return send_error("Must provide name!")

        elif len(username.strip())<4 or len(username.strip())>18:
            return send_error("Name must be between 4 and 18 of length")
        
        if not dob:
            return send_error("Must provide date of birth..!")

        elif not email:
            return send_error("Must provide email..!")

        elif not check_email(email.strip()):
            return send_error("Invalid Email")
        
        elif not inst:
            return send_error("Must provide institute..!")
        
        elif not 6<len(inst)<30:
            return send_error("Must provide valid institute..!")
        
        elif not password:
            return send_error("Must provide password..!")
        
        elif len(password)<8 or len(password) >20:
            return send_error("Invalid Password")

        elif not confirm or confirm != password:
            return send_error("Passwords don't match..!")

        # Check if user already exists
        rows = db.execute("SELECT st_id FROM student WHERE st_email = ?", (email.strip(),)).fetchall()
        if len(rows)!=0:
            return send_error("Email already exists..!")
        
        date = datetime.now().strftime("%d/%m/%y %H:%M:%S")
        db.execute("INSERT INTO student (st_name, st_email, st_dob, st_phone, st_current_inst, st_password, st_date_created) VALUES(?, ?, ?, ?, ?, ?, ?)", (username.strip().capitalize(), email.strip(), dob, phone, inst.strip().capitalize(), generate_password_hash(password), date))
        con.commit()

        return send_error("Registered..!")

    else:
        if session.get("user_id") is None:
            return render_template("signup_student.html")
        else:
            return redirect("/")
    
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