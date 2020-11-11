FROM python:latest

WORKDIR /mybot

COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]