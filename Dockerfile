FROM ubuntu:xenial
LABEL maintainer="Marron Akanishi"

# apt
RUN sed -i.bak -e "s%http://archive.ubuntu.com/ubuntu/%http://ftp.jaist.ac.jp/pub/Linux/ubuntu/%g" /etc/apt/sources.list
RUN apt update \
    && apt install -y python3 python3-pip python3-venv git cmake gcc libboost-python-dev tzdata nginx libglib2.0-0

# timezone
ENV TZ Asia/Tokyo
RUN echo "${TZ}" > /etc/timezone \
    && rm /etc/localtime \
    && ln -s /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \ 
    && rm -rf /var/lib/apt/lists/*

# setting
# nginx
ADD default.conf /etc/nginx/conf.d/
EXPOSE 80
# script
RUN git clone https://github.com/marron-akanishi/TPTS_web /usr/src/TPTS_web
WORKDIR /usr/src/TPTS_web/
ADD setting.json /usr/src/TPTS_web
RUN python3 -m venv venv \
    && . venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && deactivate

# run
CMD git pull origin
CMD /etc/init.d/nginx start \
    && . /usr/src/TPTS_web/venv/bin/activate \
    && uwsgi --ini myapp.ini

