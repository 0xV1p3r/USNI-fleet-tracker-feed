import datetime
import glob
import json
import os
import sqlite3

import rich.progress


def create_db(db_filename: str) -> None:
    con = sqlite3.connect(db_filename)
    cur = con.cursor()

    cur.execute('DROP TABLE IF EXISTS images')
    cur.execute('''CREATE TABLE images(
        id INTEGER,
        url TEXT NOT NULL,
        filename TEXT NOT NULL,
        image BLOB, 
        PRIMARY KEY (id))
    ''')

    cur.execute('DROP TABLE IF EXISTS entries')
    cur.execute('''CREATE TABLE entries(
        id INTEGER, 
        title TEXT NOT NULL, 
        url TEXT NOT NULL, 
        image INTEGER,
        date TEXT NOT NULL, 
        PRIMARY KEY (id), 
        FOREIGN KEY (image) REFERENCES images (id)
    )''')

    cur.execute('DROP TABLE IF EXISTS updates')
    cur.execute('''CREATE TABLE updates (
        id INTEGER,
        entry INTEGER,
        image INTEGER,
        date TEXT NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (entry) REFERENCES entries (id),
        FOREIGN KEY (image) REFERENCES images (id)
    )''')

    cur.close()
    con.close()

def load_entries(entry_filename: str) -> list[dict]:

    with open(entry_filename, 'r') as f:
        entries = json.loads(f.read())

    return entries

def sort_entries_by_date(entries: list[dict]) -> list[dict]:

    dates = []

    for entry in entries:
        if "Updated" in entry["date_string"]:
            date_str = entry["date_string"].split("Updated: ")[1]
        else:
            date_str = entry["date_string"]

        date = datetime.datetime.strptime(date_str, "%B %d, %Y %I:%M %p")
        dates.append(date)

    dates_sorted = dates.copy()
    dates_sorted.sort()

    sorted_entries = []
    for date in dates_sorted:
        idx = dates.index(date)
        sorted_entries.append(entries[idx])

    return sorted_entries

def split_entries_by_type(entries: list[dict]) -> tuple[list, list]:

    title_list = [entry["title"] for entry in entries]
    sorted_entries = sort_entries_by_date(entries)

    entries_list = []
    entries_titles_list = []
    updates_list = []

    for entry in sorted_entries:

        if "Updated" not in entry["date_string"]:
            # case: original entry
            entries_list.append(entry)
            entries_titles_list.append(entry["title"])
            continue

        # There to handle edge case. If the article is updated before the scraper got the original version,
        # there is no entry that is not an update.

        title_count = title_list.count(entry["title"])
        if title_count == 1 or entry["title"] not in entries_titles_list:
            entries_list.append(entry)
            entries_titles_list.append(entry["title"])
        else:
            # If there are updates to the first known entry (which is itself and update)
            updates_list.append(entry)

    return entries_list, updates_list

def get_img_urls_by_names(entries: list[dict]) -> dict:

    img_urls = {}
    for entry in entries:
        filename = os.path.splitext(entry["image_file_name"])[0]
        img_urls[filename] = entry["image_url"]

    return img_urls

def populate_images_table(db_filename: str, dir_path: str, image_urls: dict) -> None:

    if dir_path[-1] != "/":
        dir_path += "/"

    jpg_files = glob.glob(dir_path + "*.jpg")
    png_files = glob.glob(dir_path + "*.png")
    img_files = jpg_files + png_files

    con = sqlite3.connect(db_filename)
    cur = con.cursor()

    for i, img_file in rich.progress.track(enumerate(img_files), description="Populating 'images' table...", total=len(img_files)):

        with open(img_file, "rb") as f:
            img_bytes = f.read()

        rel_filepath = os.path.relpath(img_file, dir_path)
        filename = os.path.splitext(rel_filepath)[0]
        image_url = image_urls[filename]

        cur.execute(
            'INSERT INTO images (url, filename, image) VALUES (?,?,?)',
            (image_url, filename, sqlite3.Binary(img_bytes))
        )
        con.commit()

    cur.close()
    con.close()

def populate_entries_table(db_filename: str, entries: list[dict]) -> None:

    con = sqlite3.connect(db_filename)
    cur = con.cursor()

    for entry in rich.progress.track(entries, description="Populating 'entries' table..."):

        img_filename = os.path.splitext(entry["image_file_name"])[0]
        img_id = cur.execute('SELECT id FROM images WHERE filename=?', (img_filename, )).fetchone()[0]

        cur.execute(
            'INSERT INTO entries(title, url, image, date) VALUES (?,?,?,?)',
            (entry["title"], entry["article_url"], img_id, entry["date_string"])
        )
        con.commit()

    cur.close()
    con.close()

def populate_updates_table(db_filename: str, update_entries: list[dict]) -> None:

    con = sqlite3.connect(db_filename)
    cur = con.cursor()

    for entry in rich.progress.track(update_entries, description="Populating 'updates' table..."):

        img_filename = os.path.splitext(entry["image_file_name"])[0]
        img_id = cur.execute('SELECT id FROM images WHERE filename=?', (img_filename, )).fetchone()[0]
        entry_id = cur.execute('SELECT id FROM entries WHERE title=?', (entry["title"], )).fetchone()[0]

        cur.execute(
            'INSERT INTO updates(entry, image, date) VALUES (?,?,?)',
            (entry_id, img_id, entry["date_string"])
        )
        con.commit()

    cur.close()
    con.close()

if __name__ == "__main__":

    DB_NAME = "USNI-fleet-tracker.db"
    IMAGE_DIR = "./migration_data/images"
    ENTRY_FILE = "./migration_data/tracker_entries.json"

    entry_list = load_entries(ENTRY_FILE)
    original_entries, update_entries = split_entries_by_type(entry_list)
    img_url_list = get_img_urls_by_names(entry_list)

    create_db(DB_NAME)
    populate_images_table(DB_NAME, IMAGE_DIR, img_url_list)
    populate_entries_table(DB_NAME, original_entries)
    populate_updates_table(DB_NAME, update_entries)
