FROM python:3.11

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./src /app
COPY ./logger_config.ini /app/logger_config.ini
RUN echo "[]" > tracker_entries.json

CMD ["python3", "-u", "main.py"]