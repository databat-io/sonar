FROM resin/raspberrypi3-python

RUN apt-get update && apt-get install -yq --no-install-recommends \
    bluez \
    bluez-firmware \
    dnsmasq \
    pwgen \
    python-numpy \
    python-smbus && \
apt-get clean && rm -rf /var/lib/apt/lists/*

# Set our working directory
WORKDIR /usr/src/app

# Upgrade pip
RUN pip install --upgrade pip

COPY ./requirements.txt /requirements.txt

# pip install python deps from requirements.txt on the resin.io build server
RUN pip install -r /requirements.txt --no-cache-dir

# Fix for error with bluepy
RUN cd /usr/local/lib/python2.7/site-packages/bluepy && \
    make

COPY systemd/*.service /etc/systemd/system/
RUN systemctl enable redis.service && \
    systemctl enable gunicorn.service

# Copy in actual code base
COPY django /usr/src/app/
COPY start.sh /

# switch on systemd init system in container
ENV INITSYSTEM on

CMD /start.sh
