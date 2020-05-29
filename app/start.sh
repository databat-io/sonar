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
    printf "power on\ndiscoverable off\npairable off\nexit\n" | bluetoothctl

    blescan

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
