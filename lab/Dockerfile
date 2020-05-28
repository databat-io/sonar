FROM balenalib/raspberrypi3-python

ENV DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
ENV UDEV=1

RUN install_packages \
  build-essential \
  bluez \
  python-dbus \
  python-dev \
  libglib2.0-dev


COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt --no-cache-dir

CMD sleep 3600
