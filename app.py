from flask import Flask, render_template, request
import os

# Determine if we are using PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = bool(DATABASE_URL)

# Debug logging (will show in Render logs)
if USE_POSTGRES:
    print("✅ Render: Connected to PostgreSQL")
else:
    print("⚠️ Render: Falling back to SQLite")

# Use correct DB adapter
if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    def get_db_connection():
        return psycopg2.connect(DATABASE_URL, sslmode='require')
else:
    import sqlite3
    def get_db_connection():
        return sqlite3.connect('database.db')

# Create the Flask app
app = Flask(__name__)

# Initialize local database (only for local development)
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

# Show voting form
@app.route('/')
def vote_form():
    positions = {
        "President": ["Alice", "Bob"],
        "Vice President": ["Carol", "Dave"],
        "Secretary": ["Eve", "Frank"],
        "Treasurer": ["Grace", "Heidi"],
        "Sports Captain": ["Ivan", "Judy"],
        "Cultural Head": ["Mallory", "Niaj"]
    }
    return render_template('vote.html', positions=positions)

# Save vote
@app.route('/submit', methods=['POST'])
def submit_vote():
    student_id = request.form.get('student_id')
    conn = get_db_connection()
    c = conn.cursor()

    check_query = "SELECT COUNT(*) FROM votes WHERE student_id = %s" if USE_POSTGRES else "SELECT COUNT(*) FROM votes WHERE student_id = ?"
    c.execute(check_query, (student_id,))
    if c.fetchone()[0] > 0:
        conn.close()
        return "You have already voted. Only one vote per student is allowed."

    for position in request.form:
        if position == 'student_id':
            continue
        candidate = request.form[position]
        insert_query = "INSERT INTO votes (student_id, position, candidate) VALUES (%s, %s, %s)" if USE_POSTGRES else "INSERT INTO votes (student_id, position, candidate) VALUES (?, ?, ?)"
        c.execute(insert_query, (student_id, position, candidate))

    conn.commit()
    conn.close()
    return render_template('success.html')

# Show results
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

# Local dev runner
if __name__ == '__main__':
    print("Flask app is starting...")
    init_db()
    app.run(debug=True, host='0.0.0.0')