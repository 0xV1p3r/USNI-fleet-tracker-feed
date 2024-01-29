from bs4 import BeautifulSoup
from urllib.request import urlopen, Request

import re

regex_pattern = "https://news\.usni\.org/wp-content/uploads/\d{4}/\d{2}/FT_(?!.*-\d+x\d+)\S+\.jpg"
regex_pattern_thumbnail = "https://news\.usni\.org/wp-content/uploads/\d{4}/\d{2}/FT_[^\"\']+\.jpg"


def fetch_site_data(url):
    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    page = urlopen(req)
    return page.read().decode("utf-8")


def find_image_links(html):
    image_links_unsorted = re.findall(regex_pattern, html)
    thumbnail_data = image_links_unsorted.pop(0)
    thumbnail_link = re.search(regex_pattern_thumbnail, thumbnail_data).group(0)

    image_links = [thumbnail_link]

    for link in image_links_unsorted:
        if link in image_links:
            continue
        image_links.append(link)

    return image_links


def find_images(soup):
    images = soup.findAll()
