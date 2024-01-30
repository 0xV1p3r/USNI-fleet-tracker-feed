from pydantic import BaseModel
from datetime import datetime


class TrackerEntry(BaseModel):
    title: str
    article_link: str
    image_url: str
    image_file_name: str
    date_string: str
