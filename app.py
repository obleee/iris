from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from ai.question_engine import get_questions_for_role, get_question_by_id
from ai.evaluator import evaluate_answer, generate_recommendation

app = Flask(__name__)
app.secret_key = 'iris_secret_key_prototype'

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'iris.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            experience TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            question_id TEXT,
            question_text TEXT,
            answer TEXT,
            semantic_score REAL,
            keyword_score REAL,
            completeness_score REAL,
            final_score REAL,
            feedback TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/candidate')
def candidate():
    roles = [
        "Software Developer",
        "Data Analyst",
        "AI / ML Engineer",
        "Data Engineer",
        "Systems Analyst"
    ]
    return render_template('candidate.html', roles=roles)

@app.route('/start', methods=['POST'])
def start():
    session.clear()
    
    name = request.form.get('name')
    email = request.form.get('email')
    role = request.form.get('role')
    experience = request.form.get('experience')

    if not name or not email or not role or not experience:
        flash('Please fill in all candidate details.', 'danger')
        return redirect(url_for('candidate'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO candidates (name, email, role, experience) VALUES (?, ?, ?, ?)',
        (name, email, role, experience)
    )
    candidate_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session['candidate'] = {
        'id': candidate_id,
        'name': name,
        'email': email,
        'role': role,
        'experience': experience
    }
    
    # Fetch questions for role
    questions = get_questions_for_role(role, limit=5)
    
    if not questions:
        flash(f'No questions found for role "{role}". Please check questions.json data.', 'danger')
        return redirect(url_for('candidate'))

    session['question_ids'] = [q['id'] for q in questions]
    session['current_index'] = 0
    session['answers'] = []

    return redirect(url_for('interview'))

@app.route('/interview')
def interview():
    candidate_info = session.get('candidate')
    question_ids = session.get('question_ids', [])
    current_index = session.get('current_index', 0)

    if not candidate_info or not question_ids:
        return redirect(url_for('candidate'))

    if current_index >= len(question_ids):
        return redirect(url_for('results'))

    role = candidate_info['role']
    current_q_id = question_ids[current_index]
    question = get_question_by_id(role, current_q_id)

    if not question:
        flash('Question lookup error. Skipping to next.', 'warning')
        session['current_index'] += 1
        return redirect(url_for('interview'))

    return render_template(
        'interview.html',
        candidate=candidate_info,
        question=question,
        index=current_index + 1,
        total=len(question_ids)
    )

@app.route('/answer', methods=['POST'])
def answer():
    candidate_info = session.get('candidate')
    question_ids = session.get('question_ids', [])
    current_index = session.get('current_index', 0)
    user_answer = request.form.get('answer', '').strip()

    if not candidate_info or not question_ids:
        return redirect(url_for('candidate'))

    role = candidate_info['role']
    current_q_id = question_ids[current_index]
    question = get_question_by_id(role, current_q_id)

    # NLP Evaluation
    eval_res = evaluate_answer(
        user_answer=user_answer,
        reference_answer=question.get('reference_answer', ''),
        keywords=question.get('keywords', []),
        difficulty=question.get('difficulty', 'Medium')
    )

    # Record in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO interview_results 
        (candidate_id, question_id, question_text, answer, semantic_score, keyword_score, completeness_score, final_score, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        candidate_info['id'],
        current_q_id,
        question.get('question', ''),
        user_answer,
        eval_res['semantic_score'],
        eval_res['keyword_score'],
        eval_res['completeness_score'],
        eval_res['final_score'],
        eval_res['feedback']
    ))
    conn.commit()
    conn.close()

    # Save to session
    answers = session.get('answers', [])
    answers.append({
        'question_id': current_q_id,
        'question_text': question.get('question', ''),
        'answer': user_answer,
        'semantic_score': eval_res['semantic_score'],
        'keyword_score': eval_res['keyword_score'],
        'completeness_score': eval_res['completeness_score'],
        'final_score': eval_res['final_score'],
        'feedback': eval_res['feedback']
    })
    session['answers'] = answers
    session['current_index'] = current_index + 1

    return redirect(url_for('interview'))

@app.route('/results')
def results():
    candidate_info = session.get('candidate')
    answers = session.get('answers', [])

    if not candidate_info:
        return redirect(url_for('candidate'))

    if answers:
        overall_score = round(sum(a['final_score'] for a in answers) / len(answers), 1)
    else:
        overall_score = 0.0

    recommendation = generate_recommendation(overall_score)

    strengths = [a for a in answers if a['final_score'] >= 80]
    improvements = [a for a in answers if a['final_score'] < 65]

    return render_template(
        'results.html',
        candidate=candidate_info,
        answers=answers,
        overall_score=overall_score,
        recommendation=recommendation,
        strengths=strengths,
        improvements=improvements
    )

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('candidate'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)