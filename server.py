import os
from flask import Flask, abort, json, render_template

app = Flask(__name__)


def load_movie_data(movie_key):
    filepath = f'data/{movie_key}.json'
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        return json.load(f)

def load_stage_data(stage_num):
    with open('data/stages.json') as f:
        stages = json.load(f)
    return stages.get(str(stage_num))


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/learn')
def learn():
    return render_template('learn.html')

@app.route('/learn/<movie_key>/<int:stage_num>')
def learn_stage(movie_key, stage_num):
    movie = load_movie_data(movie_key)
    stage_info = load_stage_data(stage_num)

    if not movie or str(stage_num) not in movie["stages"] or not stage_info:
        abort(404)

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

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
