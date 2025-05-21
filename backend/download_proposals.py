import os
import csv
import requests

# Ensure the output folder exists
os.makedirs("pdfs", exist_ok=True)

with open("immigration_proposals.csv", newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        title = row['Title'].replace("/", "_").replace("\\", "_").strip()[:50]
        url = row['URL']
        filename = f"pdfs/{title}.pdf"

        try:
            print(f"Downloading: {title}")
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and "application/pdf" in r.headers.get("Content-Type", ""):
                with open(filename, 'wb') as f:
                    f.write(r.content)
                print(f"✅ Saved to {filename}")
            else:
                print(f"❌ Failed (Status {r.status_code})")
        except Exception as e:
            print(f"❌ Error downloading {title}: {e}")
