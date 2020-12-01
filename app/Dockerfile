FROM balenalib/raspberrypi3-python

RUN install_packages \
    bluez \
    bluez-firmware \
    build-essential \
    libpq-dev \
    python3-dev \
    python3-pip \
    python3-smbus \
    libglib2.0-dev \
    libatlas-base-dev \
    wget

# Set our working directory
WORKDIR /usr/src/app

# Fetch the latest Bluetooth company IDs
RUN wget https://raw.githubusercontent.com/NordicSemiconductor/bluetooth-numbers-database/master/v1/company_ids.json

# Upgrade pip and setuptools
RUN curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py  && \
    python3 /tmp/get-pip.py && \
    rm /tmp/get-pip.py
RUN pip3 install -U setuptools

COPY ./requirements.txt /requirements.txt

# pip install python deps from requirements.txt on the Balena's build server
RUN pip3 install -r /requirements.txt --no-cache-dir

# Copy in actual code base
COPY django /usr/src/app/
COPY start.sh /

CMD /start.sh
