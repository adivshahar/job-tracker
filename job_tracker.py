import smtplib
import sqlite3
import time
import json
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# --- Configuration ---
EMAIL = "adivshahar@gmail.com"
APP_PASSWORD = os.environ.get("EMAIL_PASSWORD", "klojbxwirdhaakxx") # Use environment variable
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DB_NAME = "jobs.db"
COMPANIES_FILE = "companies.json"
KEYWORDS = [
    "partner", "partnership", "channel", "alliance", "alliances",
    "business development", "bd", "strategic accounts", "gaming", "MEA"
]

# --- Database Functions ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sent_jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    url TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

def is_new_job(job_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT job_id FROM sent_jobs WHERE job_id = ?", (job_id,))
    result = c.fetchone()
    conn.close()
    return result is None

def mark_job_as_sent(job_id, title, company, url):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO sent_jobs (job_id, title, company, url) VALUES (?, ?, ?, ?)",
              (job_id, title, company, url))
    conn.commit()
    conn.close()

# --- Email Function ---
def send_email(jobs):
    if not jobs:
        print("No new jobs to send.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🟢 {len(jobs)} New Job Opportunities Found"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    html = "<h2>🚀 Here are your new job listings:</h2><ul>"
    for job in jobs:
        html += f"""
        <li>
            <b>{job.get('title', 'N/A')}</b> at <b>{job.get('company', 'N/A')}</b><br>
            <a href='{job.get('url', '#')}'>View Job Posting</a>
        </li>
        """
    html += "</ul><p><em>This is an automated message from your Job Tracker.</em></p>"

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, APP_PASSWORD)
            server.sendmail(EMAIL, EMAIL, msg.as_string())
        print(f"Successfully sent email with {len(jobs)} new jobs.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- Scraping Functions ---
def get_soup(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def generic_scraper(company_info):
    soup = get_soup(company_info['url'])
    if not soup:
        return []

    jobs = []
    # This is a generic selector, might need adjustment for specific sites
    job_elements = soup.select(company_info.get('job_selector', 'a'))
    
    for elem in job_elements:
        title = elem.get_text(strip=True)
        href = elem.get('href', '')
        
        # Keyword filtering
        if any(keyword in title.lower() for keyword in KEYWORDS):
            job_id = href
            full_url = href if href.startswith('http') else company_info['base_url'] + href
            
            jobs.append({
                "id": job_id,
                "title": title,
                "company": company_info['name'],
                "location": "Israel", # Assuming, can be improved
                "url": full_url
            })
    return jobs

# --- Main Logic ---
def main():
    print("Starting job tracker...")
    init_db()

    with open(COMPANIES_FILE, 'r') as f:
        companies = json.load(f)

    all_new_jobs = []

    for company in companies:
        print(f"--- Scraping {company['name']} ---")
        # In a real-world scenario, you'd call specific scraper functions
        # For now, we'll use a placeholder/generic one
        # discovered_jobs = generic_scraper(company) # Simplified for this example
        
        # Placeholder logic until individual scrapers are perfect
        discovered_jobs = []
        soup = get_soup(company['url'])
        if soup:
             # A simple example for links containing 'job' or 'career' in text or href
            for link in soup.find_all('a', href=True):
                title = link.get_text(strip=True)
                href = link.get('href')
                if any(keyword in title.lower() for keyword in KEYWORDS):
                    full_url = href if href.startswith('http') else company.get('base_url', '') + href
                    job_id = full_url # Use URL as unique ID

                    if is_new_job(job_id):
                        discovered_jobs.append({
                            "id": job_id,
                            "title": title,
                            "company": company['name'],
                            "location": "Israel",
                            "url": full_url
                        })

        if discovered_jobs:
            print(f"Found {len(discovered_jobs)} potentially new jobs at {company['name']}.")
            for job in discovered_jobs:
                 # Double-check if it's new before adding and marking
                if is_new_job(job["id"]):
                    all_new_jobs.append(job)
                    mark_job_as_sent(job["id"], job["title"], job["company"], job["url"])
        time.sleep(2) # Be polite to servers

    if all_new_jobs:
        send_email(all_new_jobs)
    else:
        print("No new relevant jobs found in this run.")
    
    print("Job tracker finished run.")

if __name__ == "__main__":
    main()
