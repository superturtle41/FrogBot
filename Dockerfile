FROM python:latest

WORKDIR /frogbot

COPY . .
RUN pip install -r requirements.txt
CMD ["python", "dbot.py"]
