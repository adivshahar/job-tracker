
import json
import requests
import sqlite3
import os
from bs4 import BeautifulSoup
from time import sleep
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Configuration
EMAIL = "adivshahar@gmail.com"
APP_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DB_NAME = "jobs.db"
COMPANIES_FILE = "all_100_companies_israel.json"
KEYWORDS = [
    "partner", "partnership", "channel", "alliance", "alliances",
    "business development", "bd", "strategic accounts", "gaming",
    "MEA", "account manager", "EMEA", "CEE"
]

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS jobs ("
        "company TEXT, "
        "url TEXT, "
        "found_keywords TEXT, "
        "PRIMARY KEY (company, url))"
    )
    conn.commit()
    conn.close()

# Save new result
def save_new_job(company, url, keywords):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO jobs (company, url, found_keywords) VALUES (?, ?, ?)",
                  (company, url, ", ".join(keywords)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Search page content
def find_keywords(text):
    return [kw for kw in KEYWORDS if kw.lower() in text.lower()]

# Send email
def send_email(new_jobs):
    if not new_jobs:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🎯 New Relevant Job Postings Found"
    msg["From"] = EMAIL
    msg["To"] = EMAIL
    html = "<h2>New Job Matches</h2><ul>"
    for job in new_jobs:
        html += f"<li><strong>{job['company']}</strong>: <a href='{job['url']}'>{job['url']}</a> <br>🔍 Matched keywords: {', '.join(job['keywords'])}</li>"
    html += "</ul>"
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)
        server.sendmail(EMAIL, EMAIL, msg.as_string())

# Main
def main():
    init_db()
    with open(COMPANIES_FILE, "r") as f:
        companies = json.load(f)

    new_matches = []

    for company in companies:
        name = company["name"]
        url = company["careers_url"]
        try:
            res = requests.get(url, timeout=10)
            if res.status_code in [200, 301]:
                soup = BeautifulSoup(res.text, "html.parser")
                text = soup.get_text()
                found = find_keywords(text)
                if found and save_new_job(name, url, found):
                    new_matches.append({"company": name, "url": url, "keywords": found})
            sleep(1)
        except Exception as e:
            print(f"Error checking {name}: {e}")

    send_email(new_matches)

if __name__ == "__main__":
    main()
