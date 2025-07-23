import json
import requests
from time import sleep

# Load company list from file
with open("all_100_companies_israel.json", "r") as f:
    companies = json.load(f)

# Check URL availability
def check_url_status(company):
    try:
        response = requests.head(company["careers_url"], timeout=10)
        return response.status_code
    except Exception as e:
        return f"Error: {e}"

def main():
    print("🔍 Checking company career pages:")
    for company in companies:
        status = check_url_status(company)
        print(f"- {company['name']}: {status}")
        sleep(0.5)  # Be polite to servers

if __name__ == "__main__":
    main()