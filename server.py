import copy
import os
import random
from flask import Flask, abort, json, redirect, render_template, session, url_for, request, jsonify, flash

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Load all JSON data
with open('data/stages.json') as f:
    all_stage_data = json.load(f)

with open('data/quiz_questions.json', 'r') as f:
    quiz_questions = json.load(f)

stories = {
    "1": {
        "name": "I am a sample story!",
        "stage_1": "In the quiet village of Alderbrook, 17-year-old Eli tends sheep, dreaming of distant lands beyond the misty mountains. His life is simple, filled with chores and the occasional festival, and he’s content—mostly.",
        "stage_2": "One evening, a dying hawk crashes at Eli’s feet, a strange scroll clutched in its talons. The scroll speaks of a fading light at the heart of the world and a key hidden deep in the Shrouded Forest—the only thing that can save it.",
        "stage_3": "Terrified, Eli dismisses the message. He's just a shepherd; adventurers are the ones who save worlds, not him. Besides, leaving means abandoning his sick mother.",
        "stage_4": "That night, an old traveler named Maelen visits the village. He seems to know about the scroll and warns Eli that ignoring the call could doom not just Alderbrook, but life itself. Maelen gives Eli an ancient pendant, saying, 'When the time comes, this will show you the way.'",
        "stage_5": "The next morning, Eli wakes to find the fields withering and the sky bruised. Driven by fear and a reluctant sense of duty, he leaves Alderbrook, clutching the pendant tightly.",
        "stage_6": "In the wilds, Eli faces treacherous rivers, shadow beasts, and betrayal. He gains allies: Kaia, a thief with a haunted past, and Brin, a warrior seeking redemption. But enemies lurk too—especially the Pale King’s riders, who seek the same key for darker purposes.",
        "stage_7": "Eli and his friends reach the Shrouded Forest’s heart: a labyrinth of living trees. They must navigate illusions, face their deepest fears, and trust each other completely to find the hidden chamber where the key rests.",
        "stage_8": "Inside the final chamber, Eli confronts the Pale King himself, who offers him a choice: hand over the pendant in exchange for the cure to his mother’s illness—or fight and risk everything. Torn, Eli almost gives in—but Kaia’s trust and Brin’s loyalty remind him who he is. He refuses and fights, barely escaping with his life and the key.",
        "stage_9": "With the key in hand, Eli unlocks a fountain of pure light that begins to heal the wounded land. His pendant melts into the key, revealing its true power: the ability to restore balance.",
        "stage_10": "Eli and his friends race back toward Alderbrook, pursued by the Pale King's remnants. Along the way, the world begins to revive—the rivers run clean, the trees regrow, and hope stirs.",
        "stage_11": "In a final confrontation at the village gates, Eli faces the Pale King one last time. Drawing on everything he’s learned—courage, sacrifice, love—he defeats the darkness, not by force, but by wielding the light to cleanse it.",
        "stage_12": "Eli returns to Alderbrook not as the sheep-boy he once was, but as a guardian of the world’s balance. His mother recovers, the village flourishes, and Eli knows that though adventures may call again, he will be ready."
    }
}
current_id = 1

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
    return render_template('home.html', stories=stories)

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
    if movie_key not in session['learn_progress']:
        session['learn_progress'][movie_key] = 1

    session['learn_progress'][movie_key] = max(stage_num + 1, session['learn_progress'][movie_key])
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
    # Reset quiz progress when starting a new quiz
    session['quiz_progress'] = {
        'current_question': 1,
        'answers': {},
        'correct_answers': 0
    }
    return redirect(url_for('hero_quiz'))

@app.route('/hero-quiz')
def hero_quiz():
    if 'quiz_progress' not in session:
        session['quiz_progress'] = {
            'current_question': 1,
            'correct_answers': 0,
            'answers': {}
        }

    current_index = session['quiz_progress']['current_question']
    
    # Ensure index is within valid range
    if current_index < 1:
        current_index = 1
    elif current_index > len(quiz_questions):
        return redirect(url_for('hero_quiz_results'))

    # question = quiz_questions[current_index - 1]

    original_question = quiz_questions[current_index - 1]
    question = copy.deepcopy(original_question)  # prevent modifying the original

     # Shuffle multiple choice options
    if question['type'] == 'multiple_choice':
        options = question['options']
        correct = question['correct_answer']
        zipped = list(enumerate(options))
        random.shuffle(zipped)
        question['options'] = [opt for _, opt in zipped]
        question['shuffled_indices'] = {i: original_i for i, (original_i, _) in enumerate(zipped)}
        question['correct_answer'] = [i for i, idx in question['shuffled_indices'].items() if idx == correct][0]
    # Shuffle matching pairs
    elif question['type'] == 'matching':
        # Shuffle terms and definitions separately for drag-and-drop matching
        terms = [{'term': pair['term']} for pair in question['pairs']]
        definitions = [{'definition': pair['definition'], 'correct_term': pair['term']} for pair in question['pairs']]

        random.shuffle(terms)
        random.shuffle(definitions)

        question['terms'] = terms
        question['definitions'] = definitions

    
    total_questions = len(quiz_questions)

    return render_template(
        'hero_quiz.html',
        question=question,
        total_questions=total_questions
    )


@app.route('/hero-quiz/submit', methods=['POST'])
def submit_hero_answer():
    data = request.get_json()
    question_num = data['question_num']
    answer = data['answer']

    # Confirm user is submitting for the current question
    if question_num != session['quiz_progress']['current_question']:
        return jsonify({
            'error': 'Submitted question number does not match session progress.'
        }), 400

    question = quiz_questions[question_num - 1]
    is_correct = False
    correct_answer_text = None  # Initialize to avoid undefined errors

    if question['type'] == 'multiple_choice':
        correct_answer_text = question['options'][question['correct_answer']]
        is_correct = answer == correct_answer_text
        if is_correct:
            session['quiz_progress']['correct_answers'] += 1
    else:
        correct_pairs = len([1 for pair in answer if pair['matched_correctly']])
        total_pairs = len(question['pairs'])
        is_correct = correct_pairs == total_pairs
        if is_correct:
            session['quiz_progress']['correct_answers'] += 1

    session['quiz_progress']['answers'][str(question_num)] = answer
    session.modified = True

    response = {
        'correct': is_correct,
        'explanation': question['explanation']
    }

    if correct_answer_text is not None:
        response['correct_answer'] = correct_answer_text

    return jsonify(response)







@app.route('/hero-quiz/next')
def next_hero_question():
    current = session['quiz_progress']['current_question']
    
    # Only allow moving forward if the current question has been answered
    if str(current) not in session['quiz_progress']['answers']:
        flash("Please answer the current question before moving on.")
        return redirect(url_for('hero_quiz'))

    session['quiz_progress']['current_question'] += 1
    session.modified = True
    print(session['quiz_progress']['current_question'])

    if session['quiz_progress']['current_question'] > len(quiz_questions):
        return redirect(url_for('hero_quiz_results'))

    return redirect(url_for('hero_quiz'))





@app.route('/hero-quiz/previous')
def previous_hero_question():
    if session['quiz_progress']['current_question'] > 1:
        session['quiz_progress']['current_question'] -= 1
        session.modified = True
    return redirect(url_for('hero_quiz'))

@app.route('/hero-quiz/results')
def hero_quiz_results():
    if 'quiz_progress' not in session:
        return redirect(url_for('hero_quiz'))

    score = (session['quiz_progress']['correct_answers'] / len(quiz_questions)) * 100
    questions_with_results = []

    for question in quiz_questions:
        question_id = str(question['id'])
        user_answer = session['quiz_progress']['answers'].get(question_id)

        result = {
            'question': question,
            'user_answer': user_answer,
            'is_correct': False
        }

        if question['type'] == 'multiple_choice':
            if user_answer and user_answer == question['options'][question['correct_answer']]:
                result['is_correct'] = True
        else:
            # For matching, we expect user_answer to be a list of dicts with matched_correctly
            matched_correctly_count = 0
            total_pairs = len(question['pairs'])
            user_pairs = user_answer if isinstance(user_answer, list) else []

            # Build a new list of pairs with correctness included
            marked_pairs = []
            matched_correctly_count = 0
            total_pairs = len(question['pairs'])

            for pair in question['pairs']:
                match = next((p for p in user_pairs if p['term'] == pair['term']), None)
                is_correct = match.get('matched_correctly', False) if match else False
                marked_pairs.append({
                    'term': pair['term'],
                    'definition': pair['definition'],
                    'matched_correctly': is_correct
                })
                if is_correct:
                    matched_correctly_count += 1

            # Replace original pairs with marked ones
            question_with_marked = question.copy()
            question_with_marked['pairs'] = marked_pairs
            result['question'] = question_with_marked

            result['is_correct'] = matched_correctly_count == total_pairs

        questions_with_results.append(result)

    return render_template('hero_quiz_results.html',
                           score=score,
                           questions_with_results=questions_with_results,
                           total_questions=len(quiz_questions))

    
@app.route('/view/<int:current_id>')
def story_urls(current_id):
   story = stories.get(str(current_id))
   print(stories)
   return render_template('story.html', story=story, all_stage_data=all_stage_data)

@app.route('/create')
def create():
    return render_template('create.html', all_stage_data=all_stage_data, stories=stories)

@app.route('/create/submit', methods=['POST'])
def submit():
    global current_id
    data = request.get_json()
    current_id += 1
    story = {
        'name': data['name'],
        'stage_1': data['stage_1'],
        'stage_2': data['stage_2'],
        'stage_3': data['stage_3'],
        'stage_4': data['stage_4'],
        'stage_5': data['stage_5'],
        'stage_6': data['stage_6'],
        'stage_7': data['stage_7'],
        'stage_8': data['stage_8'],
        'stage_9': data['stage_9'],
        'stage_10': data['stage_10'],
        'stage_11': data['stage_11'],
        'stage_12': data['stage_12']
    }
    stories[str(current_id)] = story
    return jsonify(id=current_id)

@app.route('/edit/<int:current_id>', methods=['GET', 'POST'])
def edit(current_id):
   if request.method == 'POST':
      data = request.get_json()
      stories[str(current_id)] = data
      story = stories.get(str(current_id))
      return render_template('create.html', story=story)
   elif request.method == "GET":
      item = stories.get(str(current_id))
      return render_template('create.html', story=story)

# NOTE: Dev only path to reset progress tracking
@app.route('/reset_progress')
def reset_progress():
    session.pop('learn_progress', None)
    session.pop('quiz_progress', None)
    session.pop('story_progress', None)
    return redirect(url_for('learn'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
