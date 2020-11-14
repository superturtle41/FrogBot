FROM python:3.8.6-buster

RUN apt update
RUN apt install procinfo

WORKDIR /frogbot

COPY . .
RUN pip install -r requirements.txt
CMD ["python", "dbot.py"]
