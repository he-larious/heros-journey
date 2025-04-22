mport os
from flask import Flask, abort, json, redirect, render_template, session, url_for, request, jsonify

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Load all JSON data
with open('data/stages.json') as f:
    all_stage_data = json.load(f)

with open('data/quiz.json') as f:
    quiz_data = json.load(f)

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

# Quiz routes
@app.route('/quiz')
def quiz():
    # Reset quiz progress when starting new quiz
    session['quiz_progress'] = {
        'current_question': 1,
        'correct_answers': 0,
        'answers': {},
        'stories': {}  # Add stories tracking
    }
    return render_template('quiz.html')

@app.route('/quiz/<int:question_num>')
def quiz_question(question_num):
    if 'quiz_progress' not in session:
        return redirect(url_for('quiz'))
    
    if question_num < 1 or question_num > len(quiz_data['questions']):
        abort(404)
    
    question = quiz_data['questions'][question_num - 1]
    return render_template('quiz_question.html', 
                         question=question,
                         total_questions=len(quiz_data['questions']),
                         progress=session['quiz_progress'])

@app.route('/quiz/submit', methods=['POST'])
def submit_answer():
    if 'quiz_progress' not in session:
        return redirect(url_for('quiz'))
    
    data = request.get_json()
    question_num = data.get('question_num')
    answer = data.get('answer')
    
    if not question_num or answer is None:
        abort(400)
    
    question = quiz_data['questions'][question_num - 1]
    is_correct = answer == question['correct_answer']
    
    # Update session
    if is_correct:
        session['quiz_progress']['correct_answers'] += 1
    session['quiz_progress']['answers'][str(question['id'])] = {
        'selected': answer,
        'correct': is_correct
    }
    session['quiz_progress']['current_question'] = question_num + 1
    session.modified = True
    
    return jsonify({
        'correct': is_correct,
        'explanation': question['explanation'],
        'next_question': question_num + 1 if question_num < len(quiz_data['questions']) else None
    })

@app.route('/quiz/save_story', methods=['POST'])
def save_story():
    if 'quiz_progress' not in session:
        return redirect(url_for('quiz'))
    
    data = request.get_json()
    question_num = data.get('question_num')
    story = data.get('story')
    
    if not question_num or not story:
        abort(400)
    
    # Initialize stories dict if it doesn't exist
    if 'stories' not in session['quiz_progress']:
        session['quiz_progress']['stories'] = {}
    
    # Save the story
    session['quiz_progress']['stories'][str(question_num)] = story
    session.modified = True
    
    return jsonify({'success': True})

@app.route('/quiz/results')
def quiz_results():
    if 'quiz_progress' not in session:
        return redirect(url_for('quiz'))
    
    progress = session['quiz_progress']
    total_questions = len(quiz_data['questions'])
    score = (progress['correct_answers'] / total_questions) * 100
    
    # Get all questions and their corresponding answers and stories
    questions_with_results = []
    for question in quiz_data['questions']:
        q_id = str(question['id'])
        answer_data = progress['answers'].get(q_id, {})
        story = progress.get('stories', {}).get(q_id, '')
        
        questions_with_results.append({
            'question': question,
            'answer': answer_data,
            'story': story
        })
    
    return render_template('quiz_results.html',
                         score=score,
                         correct_answers=progress['correct_answers'],
                         total_questions=total_questions,
                         questions_with_results=questions_with_results)

@app.route('/quiz/share')
def share_stories():
    if 'quiz_progress' not in session:
        return redirect(url_for('quiz'))
    
    progress = session['quiz_progress']
    stories = progress.get('stories', {})
    questions = quiz_data['questions']
    
    # Combine stories with their corresponding questions
    stories_with_questions = []
    for q_id, story in stories.items():
        question = next((q for q in questions if str(q['id']) == q_id), None)
        if question:
            stories_with_questions.append({
                'stage': question['stage'],
                'prompt': question['story_prompt'],
                'story': story
            })
    
    return render_template('share_stories.html',
                         stories=stories_with_questions)

@app.route('/quiz/stories')
def view_stories():
    # In a real application, this would fetch stories from a database
    # For now, we'll just show a message
    return render_template('view_stories.html')

# NOTE: Dev only path to reset progress tracking
@app.route('/reset_progress')
def reset_progress():
    session.pop('learn_progress', None)
    session.pop('quiz_progress', None)
    return redirect(url_for('learn'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
