from flask import Blueprint, jsonify,  redirect, render_template, session, request
from extra import required_roles
from models.quiz import Quiz


index_bp = Blueprint('index_bp', __name__)



@index_bp.route("/")
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        role = session.get("user_id")[:2]
        if role=="TA":
            return redirect("/teacher")
        elif role=="ST":
            return redirect("/student")
        




@index_bp.route("/search")
@required_roles("TA", "ST")
def search_quiz():
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify(matching_results=[])
        
        
        results = Quiz.query.with_entities(Quiz.qid, Quiz.title)\
                    .filter(Quiz.title.like(f"{query}%"))\
                    .order_by(Quiz.title)\
                    .limit(5)\
                    .all()

        
        matches = [{
            "value": quiz.title,
            "url": f"/quiz/{quiz.qid}"
        } for quiz in results]

        return jsonify(matching_results=matches)
    
    except Exception as e:
        
        return jsonify(matching_results=[]), 500