#!/bin/bash

# Make sure persistent path for db exist
mkdir -p \
    /data/redis \
    /data/collector

if [ "$GUNICORN" = "1" ]; then

    # Run migrations first
    python manage.py migrate
    python manage.py collectstatic --noinput

    /usr/local/bin/gunicorn \
        --access-logfile - \
        --bind 0.0.0.0:80 \
        --pid /tmp/pid-gunicorn \
        collector.wsgi:application

elif [ "$CELERY" = "1" ]; then
    export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
    export UDEV=1

    # Set the discoverable timeout here
    dbus-send --system --dest=org.bluez --print-reply /org/bluez/hci0 org.freedesktop.DBus.Properties.Set string:'org.bluez.Adapter1' string:'DiscoverableTimeout' variant:uint32:0 > /dev/null

    printf "Restarting bluetooth service\n"
    service bluetooth restart > /dev/null
    sleep 2

    # Redirect stdout to null, because it prints the old BT device name, which
    # can be confusing and it also hides those commands from the logs as well.
    printf "discoverable on\npairable on\nexit\n" | bluetoothctl > /dev/null

    # Start bluetooth and audio agent
    /usr/src/bluetooth-agent &

    # Temporary for debugging.
    sleep 3600

    /usr/local/bin/celery \
        -A collector \
        worker \
        -l info \
        --concurrency=2 \
        --beat
else
    echo "Unknown runtime."
fi
