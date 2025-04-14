from flask import Blueprint,  redirect, render_template, session
from app import app


index_bp = Blueprint('index_bp', __name__)


@app.route("/")
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        role = session.get("user_id")[:2]
        if role=="TA":
            return redirect("/teacher")
        elif role=="ST":
            return redirect("/student")