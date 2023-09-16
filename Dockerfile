FROM python:3

COPY requirements.txt /
COPY nagios_filter.py /
RUN pip install -r requirements.txt

CMD python -u /nagios_filter.py
