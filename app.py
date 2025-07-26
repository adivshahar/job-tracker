
from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
        # Create jobs table if it doesn't exist
    cursor.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT, position TEXT, date_posted TEXT)")

    cursor.execute("SELECT company, position, date_posted FROM jobs ORDER BY date_posted DESC")
    jobs = [{"company": row[0], "position": row[1], "date_posted": row[2]} for row in cursor.fetchall()]
    conn.close()
    return render_template("index.html", jobs=jobs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    