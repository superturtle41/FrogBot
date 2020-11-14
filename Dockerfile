FROM python:3.8.6-buster

WORKDIR /frogbot

COPY . .
RUN pip install -r requirements.txt
CMD ["python", "dbot.py"]
