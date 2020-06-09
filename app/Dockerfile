FROM balenalib/raspberrypi3-python

RUN install_packages \
    bluez \
    bluez-firmware \
    build-essential \
    libpq-dev \
    python3-pip \
    python3-dev \
    python3-smbus \
    libglib2.0-dev

# Set our working directory
WORKDIR /usr/src/app

# Upgrade pip
RUN pip3 install --upgrade pip

COPY ./requirements.txt /requirements.txt

# pip install python deps from requirements.txt on the resin.io build server
RUN pip3 install -r /requirements.txt --no-cache-dir

# Copy in actual code base
COPY django /usr/src/app/
COPY start.sh /

CMD /start.sh
