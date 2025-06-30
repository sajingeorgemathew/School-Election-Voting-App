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

# Show results
@app.route('/results')
def show_results():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT position, candidate, COUNT(*) FROM votes GROUP BY position, candidate ORDER BY position, COUNT(*) DESC")
    results = c.fetchall()
    top_candidates = {}
    for row in results:
        position, candidate, count = row
        if position not in top_candidates:
            top_candidates[position] = []
        top_candidates[position].append((candidate, count))
    conn.close()
    return render_template('results.html', results=top_candidates)

if __name__ == '__main__':
    print("Flask app is starting...")
    init_db()
    app.run(debug=True, host='0.0.0.0')
    