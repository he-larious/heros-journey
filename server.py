import os
from flask import Flask, abort, json, redirect, render_template, session, url_for
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'


with open('data/stages.json') as f:
    all_stage_data = json.load(f)

def load_movie_data(movie_key):
    """Load JSON data for a specific movie."""
    filepath = f'data/{movie_key}.json'

    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        return json.load(f)

def get_stage_info(stage_num):
    """Return stage name and description for a given stage number."""
    return all_stage_data.get(str(stage_num))

def get_stage_names():
    """Return dictionary of stage numbers → names (for diagram)"""
    return {int(k): v["name"] for k, v in all_stage_data.items()}


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/learn')
def learn():
    return render_template('learn.html')

@app.route('/learn/<movie_key>/<int:stage_num>')
def learn_stage(movie_key, stage_num):
    movie = load_movie_data(movie_key)
    stage_info = get_stage_info(stage_num)

    if not movie or str(stage_num) not in movie["stages"] or not stage_info:
        abort(404)

    # Initialize progress for this movie
    if 'learn_progress' not in session:
        session['learn_progress'] = {}

    session['learn_progress'][movie_key] = stage_num + 1
    session.modified = True

    stage = movie["stages"][str(stage_num)]

    return render_template(
        "learn_stage.html",
        movie_title=movie["title"],
        movie_key=movie_key,
        stage_num=stage_num,
        stage_name=stage_info["name"],
        stage_description=stage_info["description"],
        stage=stage
    )

@app.route('/diagram/<movie_key>')
def learn_diagram(movie_key):
    progress = session.get('learn_progress', {}).get(movie_key, 1)
    stage_names = get_stage_names()

    return render_template('diagram.html', movie_key=movie_key, stage_names=stage_names, unlocked_up_to=progress)

# NOTE: Dev only path to rest progress tracking
@app.route('/reset_progress')
def reset_progress():
    session.pop('learn_progress', None)
    return redirect(url_for('learn'))


def load_quiz_data():
    path = os.path.join("data", "quiz_questions.json")
    with open(path) as f:
        return json.load(f)

@app.route("/")
def home():
    return "<h1>Hero's Journey</h1><p><a href='/quiz/1'>Start Quiz</a></p>"

@app.route("/quiz/<int:stage_number>", methods=["GET", "POST"])
def quiz_stage(stage_number):
    quiz_data_list = load_quiz_data()
    if stage_number > len(quiz_data_list):
        return redirect(url_for("quiz_result"))

    quiz_data = quiz_data_list[stage_number - 1]
    selected = None
    feedback = None
    correct = False
    show_next = False

    if request.method == "POST":
        selected = request.form.get("answer")
        if selected == quiz_data["answer"]:
            feedback = "✅ Correct!"
            correct = True
            show_next = True
        else:
            feedback = "❌ Oops! Try again."

    return render_template(
        "quiz.html",
        quiz_data=quiz_data,
        selected=selected,
        feedback=feedback,
        correct=correct,
        show_next=show_next,
        next_stage=stage_number + 1
    )

@app.route("/quiz_result")
def quiz_result():
    return "<h2>🎉 Quiz complete! You've finished all the stages.</h2>"

if __name__ == "__main__":
    app.run(debug=True)
