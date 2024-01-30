from urllib.request import urlopen, Request
from urllib.parse import urlparse
from models import TrackerEntry
from bs4 import BeautifulSoup
from typing import List
import json
import re
import os

regex_pattern = r"https://news\.usni\.org/wp-content/uploads/\d{4}/\d{2}/FT_(?!.*-\d+x\d+)\S+\.jpg"
regex_pattern_thumbnail = r"https://news\.usni\.org/wp-content/uploads/\d{4}/\d{2}/FT_[^\"\']+\.jpg"


def fetch_site_data(url: str) -> str:
    req = Request(url=url, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(req)
    return page.read().decode("utf-8")


def find_image_links(html: str) -> List[str]:
    image_links_unsorted = re.findall(regex_pattern, html)
    thumbnail_data = image_links_unsorted.pop(0)
    thumbnail_link = re.search(regex_pattern_thumbnail, thumbnail_data).group(0)

    image_links = [thumbnail_link]

    for link in image_links_unsorted:
        if link in image_links:
            continue
        image_links.append(link)

    return image_links


def compile_tracker_entry(image_url: str, site_data: str) -> TrackerEntry:

    soup = BeautifulSoup(site_data, "html.parser")

    image_tag = soup.find("img", {"data-orig-file": image_url})
    entry_on_page = image_tag.parent.parent.parent

    entry_data = {
        "title": entry_on_page.find("h3", class_="title56 component56").a.string.strip(),
        "article_link": image_tag.parent["href"],
        "image_url": image_url,
        "image_file_name": os.path.basename(urlparse(image_url).path),
        "date_string": entry_on_page.find("div", class_="meta56__item meta56__date").string.strip()
    }

    return TrackerEntry(**entry_data)


def load_existing_entries() -> List[TrackerEntry]:

    with open("./tracker_entries.json", "r") as file:
        entries = json.load(file)

    return entries


def update_existing_entries(entries: List[TrackerEntry]) -> None:

    data_to_be_written = []

    for entry in entries:
        data_to_be_written.append(dict(entry))

    with open("./tracker_entries.json", "w") as file:
        file.write(json.dumps(data_to_be_written))


def check_for_new_entries(entry_list: List[TrackerEntry], existing_entries: List[TrackerEntry]) -> List[TrackerEntry]:

    new_entries: List[TrackerEntry] = []

    for entry in entry_list:

        already_exists = False

        for existing_entry in existing_entries:
            if dict(entry) == dict(existing_entry):
                already_exists = True
                break

        if not already_exists:
            new_entries.append(entry)

    return new_entries


def fetch() -> List[TrackerEntry]:
    site_data = fetch_site_data("https://news.usni.org/category/fleet-tracker")
    image_url_list = find_image_links(site_data)

    entry_list: List[TrackerEntry] = []

    for url in image_url_list:
        entry = compile_tracker_entry(url, site_data)
        entry_list.append(entry)

    existing_entries = load_existing_entries()
    new_entries = check_for_new_entries(entry_list=entry_list, existing_entries=existing_entries)

    if new_entries:
        existing_entries.extend(new_entries)
        update_existing_entries(existing_entries)

    return new_entries
