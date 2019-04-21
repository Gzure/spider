FROM ubuntu:16.04

MAINTAINER ben.zuo "ben.zuo@pica8.com"

# install python-pip
RUN apt-get update -y && apt-get install gcc  python-pip python-dev build-essential language-pack-zh-hans -y

# copy server
RUN mkdir /work
RUN mkdir /work/spider
WORKDIR /work/spider
COPY crawlers/ ./crawlers
COPY static/ ./static
COPY requirements.txt .
RUN touch spider.log
COPY *.py ./
RUN pip install -r requirements.txt
EXPOSE 8888

# run
CMD ["/usr/bin/python","spider.py"]