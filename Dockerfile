FROM python:3.8.6-alpine

RUN apt-get install -y procinfo

WORKDIR /frogbot

COPY . .
RUN pip install -r requirements.txt
CMD ["python", "dbot.py"]
