#!/bin/bash

# Make sure persistent path for db exist
mkdir -p \
    /data/redis \
    /data/collector

if [ "$GUNICORN" = "1" ]; then

    # Run migrations first
    python3 manage.py migrate
    python3 manage.py collectstatic --noinput

    /usr/local/bin/gunicorn \
        --access-logfile - \
        --bind 0.0.0.0:80 \
        --pid /tmp/pid-gunicorn \
        collector.wsgi:application

elif [ "$CELERY" = "1" ]; then
    if [ "$DEV_MODE" = "1" ]; then
        echo "Running in development mode. Not initiating Bluetooth."
    else
        export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
        export UDEV=1

        # Enable Bluetooth module
        printf "power on\ndiscoverable off\npairable off\nexit\n" | bluetoothctl
    fi

    /usr/local/bin/celery \
        -A collector \
        worker \
        -l info \
        --concurrency=2 \
        --beat
else
    echo "Unknown runtime."
fi
