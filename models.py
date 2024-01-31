from pydantic import BaseModel


class TrackerEntry(BaseModel):
    title: str
    article_url: str
    image_url: str
    image_file_name: str
    date_string: str
