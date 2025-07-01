from flask import Flask, render_template, request
import sqlite3

# Create the Flask app
app = Flask(__name__)

# Initialize the database
def init_db():
    conn = sqlite3.connect('database.db')
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
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Check if student already voted
    c.execute("SELECT COUNT(*) FROM votes WHERE student_id = ?", (student_id,))
    if c.fetchone()[0] > 0:
        conn.close()
        return "You have already voted. Only one vote per student is allowed."

    # Save each vote per position
    for position in request.form:
        if position == 'student_id':
            continue
        candidate = request.form[position]
        c.execute("INSERT INTO votes (student_id, position, candidate) VALUES (?, ?, ?)", (student_id, position, candidate))

    conn.commit()
    conn.close()
    return render_template('success.html')

@app.route('/results')
def results():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        SELECT position, candidate, vote_count FROM (
            SELECT position, candidate, COUNT(*) AS vote_count,
                   RANK() OVER (PARTITION BY position ORDER BY COUNT(*) DESC) AS rank
            FROM votes
            GROUP BY position, candidate
        )
        WHERE rank = 1;
    ''')
    results = c.fetchall()
    conn.close()
    return render_template('results.html', results=results)

if __name__ == '__main__':
    print("Flask app is starting...")
    init_db()
    app.run(debug=True, host='0.0.0.0')
    