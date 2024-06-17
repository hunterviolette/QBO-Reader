FROM ubuntu:jammy-20240530

WORKDIR /root

COPY ./requirements.txt ./

RUN apt-get update && \
    apt-get install -y vim python3.10 python3-pip && \
    pip3 install --upgrade setuptools wheel

RUN pip3 install --no-cache-dir -r requirements.txt 

COPY ./src ./