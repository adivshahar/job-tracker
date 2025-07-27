import os
import json
import sqlite3
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime

# Configuration
EMAIL = "adivshahar8@gmail.com"
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DB_NAME = "jobs.db"

# Compute the absolute path to the companies file relative to this script
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
COMPANIES_FILE = os.path.join(DATA_DIR, 'all_100_companies_israel.json')

LOG_FILE = "job_tracker.log"

KEYWORDS = [
    "partner", "partnership", "channel", "alliances",
    "business development", "bd", "strategic accounts", "gaming",
    "MEA", "EMEA", "CEE", "account manager"
]

# Logging setup
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(message)s")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS sent_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT UNIQUE, company TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT, position TEXT, date_posted TEXT)")
    conn.commit()
    conn.close()

def is_new_job(job_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT job_id FROM sent_jobs WHERE job_id = ?", (job_id,))
    result = c.fetchone()
    conn.close()
    return result is None

def mark_job_as_sent(job_id, company):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO sent_jobs (job_id, company) VALUES (?, ?)", (job_id, company))
    conn.commit()
    conn.close()

def add_job_to_db(company, position, date_posted):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO jobs (company, position, date_posted) VALUES (?, ?, ?)", (company, position, date_posted))
    conn.commit()
    conn.close()

def load_companies():
    with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_link(href, base_url):
    if not href.startswith("http"):
        return urljoin(base_url, href)
    return href

def scrape_jobs_from_page(company_name, url):
    jobs = []
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        base_url = url.rstrip("/")
        links = soup.find_all("a", href=True)
        for link in links:
            text = link.get_text().strip()
            if not text:
                continue
            href = link["href"]
            full_url = clean_link(href, base_url).rstrip("/")
            # skip general job listing pages
            if full_url == base_url or full_url.endswith("/careers") or full_url.endswith("/jobs"):
                continue
            for kw in KEYWORDS:
                if kw.lower() in text.lower():
                    job_id_part = full_url.split("/")[-1][:64]
                    job_id = f"{company_name}_{job_id_part}"
                    jobs.append({"id": job_id, "title": text.title(), "url": full_url})
                    break
    except Exception as e:
        logging.error(f"Error checking {company_name}: {e}")
    return jobs

def send_email(jobs):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🌐 New Job Opportunities Found"
    msg["From"] = EMAIL
    msg["To"] = EMAIL
    html = "<h2>🧵 New Relevant Job Listings:</h2><ul>"
    for job in jobs:
        html += f"<li><b>{job['title']}</b><br><a href='{job['url']}'>{job['url']}</a></li>"
    html += "</ul>"
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, EMAIL_PASSWORD)
            server.sendmail(EMAIL, EMAIL, msg.as_string())
    except Exception as e:
        logging.error(f"Email send failed: {e}")

def main():
    init_db()
    companies = load_companies()
    new_jobs = []
    for company in companies:
        name = company.get("name", "Unknown")
        url = company.get("careers_url")
        if url:
            found_jobs = scrape_jobs_from_page(name, url)
            for job in found_jobs:
                if is_new_job(job["id"]):
                    mark_job_as_sent(job["id"], name)
                    add_job_to_db(name, job["title"], datetime.now().strftime("%Y-%m-%d"))
                    new_jobs.append(job)
    if new_jobs:
        send_email(new_jobs)

if __name__ == "__main__":
    main()
