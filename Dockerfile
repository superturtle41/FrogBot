FROM python:latest

WORKDIR /mybot

COPY /path/to/ur/bot .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]