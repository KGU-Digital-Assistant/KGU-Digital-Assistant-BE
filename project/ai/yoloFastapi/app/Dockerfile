# backend/Dockerfile


# pull official base image
FROM python:3.10.6-slim-buster

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /usr/src/app

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc \
  && apt-get -y install libgl1-mesa-glx \
  && apt-get -y install libglib2.0-0 \
  && apt-get -y install default-libmysqlclient-dev \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip \
  && pip install --upgrade setuptools
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /usr/src/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]