FROM python:3

RUN pip install pika requests

COPY nagios_filter.py /

CMD python -u /nagios_filter.py
