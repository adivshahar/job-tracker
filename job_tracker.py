import smtplib
import sqlite3
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
EMAIL = "adivshahar@gmail.com"
APP_PASSWORD = "klojbxwirdhaakxx"  # Do not share this again
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DB_NAME = "jobs.db"

# Dummy example of new jobs (would be dynamically scraped in full version)
new_jobs = [
    {"id": "123", "title": "Partner Manager - TikTok", "company": "TikTok", "location": "Tel Aviv", "url": "https://careers.tiktok.com/job/123"},
    {"id": "456", "title": "Channel Sales Manager - Meta", "company": "Meta", "location": "Tel Aviv", "url": "https://www.metacareers.com/job/456"}
]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sent_jobs (job_id TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def is_new_job(job_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT job_id FROM sent_jobs WHERE job_id = ?", (job_id,))
    result = c.fetchone()
    conn.close()
    return result is None

def mark_job_as_sent(job_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO sent_jobs (job_id) VALUES (?)", (job_id,))
    conn.commit()
    conn.close()

def send_email(jobs):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🟢 New Job Opportunities for You"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    html = "<h2>🚀 New Job Listings:</h2><ul>"
    for job in jobs:
        html += f"<li><b>{job['title']}</b> at {job['company']} – {job['location']}<br><a href='{job['url']}'>{job['url']}</a></li>"
    html += "</ul>"

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)
        server.sendmail(EMAIL, EMAIL, msg.as_string())

def main():
    init_db()
    unsent_jobs = []
    for job in new_jobs:
        if is_new_job(job["id"]):
            unsent_jobs.append(job)
            mark_job_as_sent(job["id"])
    if unsent_jobs:
        send_email(unsent_jobs)

if __name__ == "__main__":
    main()