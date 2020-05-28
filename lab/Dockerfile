FROM balenalib/%%BALENA_MACHINE_NAME%%-debian:stretch

ENV DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
ENV UDEV=1

RUN install_packages \
  bluez \
  python-dbus \
  python-dev \
  libglib2.0-dev


COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt --no-cache-dir

CMD sleep 3600
