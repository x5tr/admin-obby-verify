FROM python:3.8-slim-buster

WORKDIR /app
RUN apt-get update && apt-get install tk-dev -y
RUN apt-get install git -y
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ARG PORT=8000
ENV PORT=$PORT
COPY . .

CMD ["gunicorn", "web:app"]