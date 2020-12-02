FROM balenalib/rpi-raspbian:buster

RUN install_packages \
    bluez \
    bluez-firmware \
    build-essential \
    curl \
    libpq-dev \
    python3-dev \
    python3-pip \
    python3-smbus \
    libglib2.0-dev \
    libatlas-base-dev

# Set our working directory
WORKDIR /usr/src/app

# Works around issue with `curl`
# https://github.com/balena-io-library/base-images/issues/562
RUN c_rehash

# Fetch the latest Bluetooth company IDs
RUN curl -s -o company_ids.json \
    https://raw.githubusercontent.com/NordicSemiconductor/bluetooth-numbers-database/master/v1/company_ids.json

COPY ./requirements.txt /requirements.txt

# pip install python deps from requirements.txt on the Balena's build server
RUN pip3 install -U setuptools --no-cache-dir
RUN pip3 install -r /requirements.txt --no-cache-dir

# Copy in actual code base
COPY django /usr/src/app/
COPY start.sh /

CMD /start.sh
