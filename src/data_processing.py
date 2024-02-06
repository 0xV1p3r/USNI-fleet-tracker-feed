from urllib.request import urlopen, Request
from urllib.parse import urlparse
from models import TrackerEntry
from bs4 import BeautifulSoup
from typing import List
import requests
import logging
import json
import re
import os

logger = logging.getLogger("data")

regex_pattern_article_url = r"https://news\.usni\.org/\d{4}/\d{2}/\d{2}/usni-news-fleet-and-marine-tracker-\S+"
regex_pattern_article_url_tail = r"/ft_\d+_\d+_\d+(-\d+)?|ft_\d+_\d+_\d+"
regex_pattern_image_url = r"https://news\.usni\.org/wp-content/uploads/\d{4}/\d{2}/FT_(?!.*-\d+x\d+)\S+\.jpg"


def fetch_site_data(url: str) -> str:
    logger.debug(f"Function fetch_site_data called for '{url}'")
    req = Request(url=url, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(req)
    return page.read().decode("utf-8")


def find_image_url(html: str) -> str:
    result = re.findall(regex_pattern_image_url, html)
    logger.debug(f"Function find_image_url called with result: '{result[0]}'")
    return result[0]


def find_article_urls(html: str) -> List[str]:

    logger.debug("Function find_article_urls called")

    article_urls_raw: List[str] = re.findall(regex_pattern_article_url, html)
    article_urls: List[str] = []

    for url in article_urls_raw:

        if re.search(regex_pattern_article_url_tail, url):
            continue

        url = url.replace(r'\ ', '')
        url = url.replace('"', '')
        url = url.replace('>', '')

        if url in article_urls:
            continue

        article_urls.append(url)

        logger.debug(f"Function find_article_urls: found '{url}'")

    logger.debug(f"Function find_article_urls: found {len(article_urls)} article URLs")

    return article_urls


def compile_tracker_entry(article_url: str) -> TrackerEntry:

    html = fetch_site_data(url=article_url)
    image_url = find_image_url(html=html)
    soup = BeautifulSoup(html, "html.parser")

    entry_data = {
        "title": soup.find("h1", class_="post-title single56__title component56").string.strip(),
        "article_url": article_url,
        "image_url": image_url,
        "image_file_name": os.path.basename(urlparse(image_url).path),
        "date_string": soup.find("div", class_="meta56__item meta56__date").string.strip()
    }

    logger.debug(f"Function compile_tracker_entry called with result: '{entry_data}'")

    return TrackerEntry(**entry_data)


def load_existing_entries() -> List[TrackerEntry]:

    logger.debug("Function load_existing_entries called")

    with open("./tracker_entries.json", "r") as file:
        data = file.read()

    try:
        return json.loads(data)
    except json.decoder.JSONDecodeError:
        logger.warning("No existing entries found!")
        return []


def update_existing_entries(entries: List[TrackerEntry]) -> None:

    logger.debug("Function update_existing_entries called")

    data_to_be_written = []

    for entry in entries:
        data_to_be_written.append(dict(entry))

    with open("./tracker_entries.json", "w") as file:
        file.write(json.dumps(data_to_be_written))


def check_for_new_entries(entry_list: List[TrackerEntry], existing_entries: List[TrackerEntry]) -> List[TrackerEntry]:

    logger.debug("Function check_for_new_entries called")

    new_entries: List[TrackerEntry] = []

    for entry in entry_list:

        already_exists = False

        for existing_entry in existing_entries:
            if dict(entry) == dict(existing_entry):
                already_exists = True
                break

        if not already_exists:
            new_entries.append(entry)

    logger.debug(f"Function check_for_new_entries: found {len(new_entries)} new entries")

    return new_entries


def fetch() -> List[TrackerEntry]:
    site_data = fetch_site_data("https://news.usni.org/category/fleet-tracker")
    article_urls = find_article_urls(html=site_data)

    entry_list: List[TrackerEntry] = []

    for url in article_urls:
        entry = compile_tracker_entry(article_url=url)
        entry_list.append(entry)

    existing_entries = load_existing_entries()
    new_entries = check_for_new_entries(entry_list=entry_list, existing_entries=existing_entries)
    new_entries.reverse()

    if new_entries:
        new_entries.extend(existing_entries)
        update_existing_entries(new_entries)

        for entry in new_entries:
            fetch_image(url=entry["image_url"], file_name=entry["image_file_name"])

    return new_entries


def fetch_image(url: str, file_name: str) -> None:

    logger.debug(f"Fetching image from {url}...")

    image_data = requests.get(url).content

    if not os.path.exists("./images"):
        os.mkdir("./images")

    with open(f"./images/{file_name}", mode="wb") as f:
        f.write(image_data)

    logger.debug(f"Saved image to {file_name}")
