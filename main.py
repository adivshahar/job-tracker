
import smtplib
import sqlite3
import requests
import json
import os
import logging
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urljoin

# Configuration
EMAIL = "adivshahar@gmail.com"
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DB_NAME = "jobs.db"
COMPANIES_FILE = "data/companies.json"
LOG_FILE = "job_tracker.log"

KEYWORDS = [
    "partner", "partnership", "channel", "alliances",
    "business development", "bd", "strategic accounts", "gaming",
    "MEA", "EMEA", "CEE", "account manager"
]

# Logging setup
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS sent_jobs (job_id TEXT PRIMARY KEY)")
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
        links = soup.find_all("a", href=True)

        for link in links:
            text = link.get_text().strip().lower()
            href = clean_link(link["href"], url)
            if any(k in text for k in KEYWORDS):
                job_id = href.split("/")[-1][:64]
                jobs.append({
                    "id": f"{company_name}_{job_id}",
                    "title": text.title(),
                    "url": href
                })
    except Exception as e:
        logging.error(f"Error checking {company_name}: {e}")
    return jobs

def send_email(jobs):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🟢 New Job Opportunities Found"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    html = "<h2>🚀 New Relevant Job Listings:</h2><ul>"
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
                    mark_job_as_sent(job["id"])
                    new_jobs.append(job)
    if new_jobs:
        send_email(new_jobs)

if __name__ == "__main__":
    main()
