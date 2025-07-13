# site_index_builder.py
# Requires: requests, beautifulsoup4

import os
import re
import json
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime

# SETTINGS
LOCAL_SITE_DIR = "./site_copy"  # Where you store downloaded HTML files
PEOPLE_INDEX_PATH = "people_index.json"
PAGE_INDEX_PATH = "page_index.json"

# UTILITIES
def get_file_info(filepath):
    stat = os.stat(filepath)
    return {
        "size": stat.st_size,
        "last_modified": datetime.utcfromtimestamp(stat.st_mtime).isoformat()
    }

def extract_year(text):
    match = re.search(r'(\d{4})(?:-(\d{2,4}))?', text)
    if match:
        start = match.group(1)
        end = match.group(2) or start
        end = start[:2] + end if len(end) == 2 else end
        return start, end
    return None, None

# MAIN PARSER

def parse_people_from_html(filepath, region):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string.strip() if soup.title else os.path.basename(filepath)
    location = title.replace("Photo Album", "").strip()

    people = []
    current_year = None
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li']):
        text = tag.get_text(strip=True)
        year_start, year_end = extract_year(text)
        if year_start:
            current_year = f"{year_start}-{year_end}" if year_start != year_end else year_start
            continue

        if current_year and ',' in text:
            names = [n.strip() for n in text.split(',') if len(n.strip()) > 2]
            for name in names:
                if any(c.isalpha() for c in name):
                    people.append({
                        "name": name,
                        "region": region,
                        "location": location,
                        "detachment": current_year,
                        "year_start": year_start,
                        "year_end": year_end,
                        "link": os.path.relpath(filepath, LOCAL_SITE_DIR).replace('\\', '/')
                    })
    return people

# INDEX BUILDER

def build_indexes():
    if os.path.exists(PAGE_INDEX_PATH):
        with open(PAGE_INDEX_PATH) as f:
            old_index = json.load(f)
    else:
        old_index = {}

    new_index = {}
    all_people = []

    for root, _, files in os.walk(LOCAL_SITE_DIR):
        for file in files:
            if file.endswith(".html"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, LOCAL_SITE_DIR)
                region = rel_path.split(os.sep)[0]
                info = get_file_info(full_path)
                new_index[rel_path] = info

                if rel_path not in old_index or old_index[rel_path]['size'] != info['size']:
                    print(f"[UPDATED] {rel_path}")
                    all_people.extend(parse_people_from_html(full_path, region))
                else:
                    print(f"[SKIPPED] {rel_path}")

    with open(PEOPLE_INDEX_PATH, 'w') as f:
        json.dump(all_people, f, indent=2)

    with open(PAGE_INDEX_PATH, 'w') as f:
        json.dump(new_index, f, indent=2)

    print(f"\n✅ Indexing complete. Found {len(all_people)} person entries.")

if __name__ == "__main__":
    build_indexes()
