FROM balenalib/raspberrypi3-python

RUN install_packages \
    bluez \
    bluez-firmware \
    build-essential \
    dnsmasq \
    pwgen \
    python-dev \
    python-numpy \
    python-smbus \
    libglib2.0-dev

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

# Copy in actual code base
COPY django /usr/src/app/
COPY start.sh /

CMD /start.sh
