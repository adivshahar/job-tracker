import json
import requests
from time import sleep

# Load company list from file
with open("all_100_companies_israel.json", "r", encoding="utf-8") as f:
    companies = json.load(f)

# Check URL availability
def check_url_status(company):
    try:
        response = requests.head(company["careers_url"], timeout=10)
        return response.status_code
    except Exception as e:
        return f"Error: {e}"

def main():
    print("🚀 Starting job tracker check...\n")
    print(f"Total companies to check: {len(companies)}\n")

    for i, company in enumerate(companies, start=1):
        print(f"🔍 [{i}] Checking: {company['name']} - {company['careers_url']}")
        status = check_url_status(company)
        print(f"➡️ Status: {status}\n")
        sleep(0.5)  # To avoid hammering servers

    print("✅ Job tracker scan completed.")

if __name__ == "__main__":
    main()
