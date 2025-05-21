import csv
from datetime import datetime
import os

LOG_FILE = "scan_log.csv"

def log_scan(filename, text, label, distance, used_keywords=False):
    write_header = not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0

    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["Timestamp", "Filename", "Label", "Distance", "Used Keywords", "Preview"])


        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            filename,
            label,
            round(distance, 4),
            "YES" if used_keywords else "NO",
            text[:100].replace("\n", " ") + "..."
        ])

