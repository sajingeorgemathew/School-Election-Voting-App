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

# --- ADMIN CREDENTIAL ---
ADMIN_PASSWORD = "letmein123"  # 🔐 Change this to your own admin password!

# --- LOAD VALID STUDENT IDS ---
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

# 🔐 ADMIN LOGIN PAGE
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('results'))
        return "❌ Incorrect admin password."
    return render_template('admin_login.html')

# 🔐 LOGOUT ADMIN
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Step 1: Login with Student ID
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

# Step 2: Voting Page
@app.route('/vote')
def vote_form():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    positions = {
        "Head Girl": ["Niveditha", "Nandhana"],
        "Asst. Head Girl": ["Vaiga", "Jovitha", "Diya"],
        "Vice Sports Captain": ["Harinandana", "Neeraja", "Avandhika", "Devaduth", "Vivek", "Niranjan", "Nakshakthra"]
    }

    return render_template('vote.html', positions=positions)


# Step 3: Handle Submission
@app.route('/submit', methods=['POST'])
def submit_vote():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    check_query = "SELECT COUNT(*) FROM votes WHERE student_id = %s" if USE_POSTGRES else "SELECT COUNT(*) FROM votes WHERE student_id = ?"
    c.execute(check_query, (student_id,))
    if c.fetchone()[0] > 0:
        conn.close()
        return "You have already voted."

    for position in request.form:
        if position == 'csrf_token':
            continue
        candidate = request.form[position]
        insert_query = "INSERT INTO votes (student_id, position, candidate) VALUES (%s, %s, %s)" if USE_POSTGRES else "INSERT INTO votes (student_id, position, candidate) VALUES (?, ?, ?)"
        c.execute(insert_query, (student_id, position, candidate))

    conn.commit()
    conn.close()
    session.clear()
    return render_template('success.html')

# ✅ 🔐 Admin-only Results
@app.route('/results')
def results():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = get_db_connection()
    c = conn.cursor()

    query = '''
        SELECT position, candidate, COUNT(*) AS vote_count
        FROM votes
        GROUP BY position, candidate
        ORDER BY position, vote_count DESC;
    '''
    c.execute(query)
    rows = c.fetchall()
    conn.close()

    from collections import defaultdict
    grouped_results = defaultdict(list)
    for row in rows:
        position, candidate, vote_count = row
        grouped_results[position].append({
            'candidate': candidate,
            'votes': vote_count
        })

    return render_template('results.html', grouped_results=grouped_results)


# ✅ 🔐 Admin-only Reset Route
@app.route('/reset_votes')
def reset_votes():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM votes")
    conn.commit()
    conn.close()
    return "✅ All votes cleared successfully!"

# Run app locally
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')