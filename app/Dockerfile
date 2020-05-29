FROM balenalib/raspberrypi3-python

RUN install_packages \
    bluez \
    bluez-firmware \
    build-essential \
    dnsmasq \
    pwgen \
    python-dbus \
    python-dev \
    python-gobject \
    python-gpiozero \
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

COPY udev-rules/ /etc/udev/rules.d/

COPY bluetooth-udev /usr/src/
RUN chmod +x /usr/src/bluetooth-udev

COPY bluetooth-agent /usr/src/
RUN chmod +x /usr/src/bluetooth-agent

# Fix for error with bluepy
RUN cd /usr/local/lib/python2.7/site-packages/bluepy && \
    make

# Copy in actual code base
COPY django /usr/src/app/
COPY start.sh /

CMD /start.sh
