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
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    for position in request.form:
        candidate = request.form[position]
        c.execute("INSERT INTO votes (position, candidate) VALUES (?, ?)", (position, candidate))
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
    