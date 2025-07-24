import json
import requests
from time import sleep

# Load company list from file
try:
    with open("all_100_companies_israel.json", "r", encoding="utf-8") as f:
        companies = json.load(f)
    print(f"✅ Loaded {len(companies)} companies.")
except Exception as e:
    print(f"❌ Failed to load company list: {e}")
    exit(1)

# Check URL availability
def check_url_status(company):
    try:
        response = requests.head(company["careers_url"], timeout=10)
        return response.status_code
    except Exception as e:
        return f"Error: {e}"

def main():
    print("🚀 Starting job tracker check...\n")

    for i, company in enumerate(companies, start=1):
        name = company.get("name")
        url = company.get("careers_url")
        if not url:
            print(f"⚠️ No careers URL for {name}")
            continue

        print(f"🔍 [{i}] Checking: {name} - {url}")
        status = check_url_status(company)
        print(f"➡️ Result: {status}\n")
        sleep(0.5)

    print("✅ All done.")

if __name__ == "__main__":
    main()
