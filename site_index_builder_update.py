# site_index_builder_updated.py
# Updated to fix region, rename detachment, and clean data output

import os
import re
import json
from bs4 import BeautifulSoup

# Configuration
LOCAL_SITE_DIR = "./site_copy"  # Where your HTML files live
PEOPLE_INDEX_PATH = "people_index.json"
PAGE_INDEX_PATH = "page_index.json"

# Region path to label mapping
region_map = {
    "south-asia": "Region 1",
    "africa": "Region 2",
    "europe": "Region 3",
    "americas": "Region 4",
    "east-asia": "Region 5",
    "middle-east": "Region 6",
    "australia": "Region 7",
    "misc": "Deactivated Detachments",
}

# Detect year string like 2008 or 1995-97
def extract_year(text):
    match = re.search(r'(\d{4})(?:-(\d{2,4}))?', text)
    if match:
        return match.group(0)  # e.g. "2008" or "1995-97"
    return None

# Parse HTML and extract people entries from detachment history blocks
def parse_people_from_html(filepath, region):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')

    location = soup.title.string.strip() if soup.title else os.path.basename(filepath)
    people = []
    current_detachment_date = None

    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li']):
        text = tag.get_text(separator=' ', strip=True)
        date = extract_year(text)
        if date:
            current_detachment_date = date
            continue

        if current_detachment_date and ',' in text:
            names = [n.strip() for n in text.split(',') if len(n.strip()) > 2]
            for name in names:
                if any(c.isalpha() for c in name):
                    people.append({
                        "name": name,
                        "region": region,
                        "location": location,
                        "detachment_date": current_detachment_date,
                        "link": os.path.relpath(filepath, LOCAL_SITE_DIR).replace('\\', '/')
                    })

    return people

# Main builder function
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

                # Determine region based on folder path
                parts = rel_path.split(os.sep)
                region_key = parts[2] if len(parts) >= 3 else "misc"
                region = region_map.get(region_key, "Unknown Region")

                size = os.stat(full_path).st_size
                last = old_index.get(rel_path, {}).get("size")
                new_index[rel_path] = {"size": size}

                if last != size:
                    print(f"[UPDATED] {rel_path}")
                    people = parse_people_from_html(full_path, region)
                    all_people.extend(people)
                else:
                    print(f"[SKIPPED] {rel_path}")

    with open(PEOPLE_INDEX_PATH, 'w') as f:
        json.dump(all_people, f, indent=2)

    with open(PAGE_INDEX_PATH, 'w') as f:
        json.dump(new_index, f, indent=2)

    print(f"\n✅ Done! {len(all_people)} people indexed.")

if __name__ == '__main__':
    build_indexes()
