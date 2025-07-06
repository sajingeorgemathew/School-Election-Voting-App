from flask import Flask, render_template, request, redirect, session, url_for
import os
import pandas as pd

# --- DATABASE SETUP ---
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    print("Render: Connected to PostgreSQL")
    import psycopg2
    def get_db_connection():
        return psycopg2.connect(DATABASE_URL, sslmode='require')
else:
    print("Render: Falling back to SQLite")
    import sqlite3
    def get_db_connection():
        return sqlite3.connect('database.db')

# --- APP CONFIGURATION ---
app = Flask(__name__)
app.secret_key = 'school-elect7'  # Required for sessions

# --- LOAD VALID STUDENT IDS FROM EXCEL ---
valid_ids = set(pd.read_excel("student_ids.xlsx")['Student_ID'].astype(str).str.strip())

# --- DB INITIALIZATION FOR LOCAL ---
def init_db():
    if not USE_POSTGRES:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                position TEXT,
                candidate TEXT
            )
        ''')
        conn.commit()
        conn.close()

# --- ROUTES ---

# Step 1: Login with ID
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id').strip()
        if student_id not in valid_ids:
            return "❌ Invalid ID. Please contact the teacher."
        
        conn = get_db_connection()
        c = conn.cursor()
        query = "SELECT COUNT(*) FROM votes WHERE student_id = %s" if USE_POSTGRES else "SELECT COUNT(*) FROM votes WHERE student_id = ?"
        c.execute(query, (student_id,))
        if c.fetchone()[0] > 0:
            conn.close()
            return "⚠️ You have already voted."

        conn.close()
        session['student_id'] = student_id
        return redirect(url_for('vote_form'))

    return render_template('login.html')

# Step 2: Show Voting Form
@app.route('/vote')
def vote_form():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    positions = {
        "President": ["Alice", "Bob"],
        "Vice President": ["Carol", "Dave"],
        "Secretary": ["Eve", "Frank"],
        "Treasurer": ["Grace", "Heidi"],
        "Sports Captain": ["Ivan", "Judy"],
        "Cultural Head": ["Mallory", "Niaj"]
    }
    return render_template('vote.html', positions=positions)

# Step 3: Handle Vote Submission
@app.route('/submit', methods=['POST'])
def submit_vote():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    for position in request.form:
        candidate = request.form[position]
        insert_query = "INSERT INTO votes (student_id, position, candidate) VALUES (%s, %s, %s)" if USE_POSTGRES else "INSERT INTO votes (student_id, position, candidate) VALUES (?, ?, ?)"
        c.execute(insert_query, (student_id, position, candidate))

    conn.commit()
    conn.close()
    session.clear()  # Prevent back-voting
    return render_template('success.html')

# Results Page
@app.route('/results')
def results():
    conn = get_db_connection()
    c = conn.cursor()
    query = '''
        SELECT position, candidate, vote_count FROM (
            SELECT position, candidate, COUNT(*) AS vote_count,
                   RANK() OVER (PARTITION BY position ORDER BY COUNT(*) DESC) AS rank
            FROM votes
            GROUP BY position, candidate
        ) AS ranked
        WHERE rank = 1;
    '''
    c.execute(query)
    results = c.fetchall()
    conn.close()
    return render_template('results.html', results=results)

# Run locally
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')
