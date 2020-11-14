FROM python:latest

RUN sudo apt-get install -y procinfo

WORKDIR /frogbot

COPY . .
RUN pip install -r requirements.txt
CMD ["python", "dbot.py"]
