#!/bin/bash

# Make sure persistent path for db exist
mkdir -p \
    /data/redis \
    /data/collector

SOFT_COUNTER=0
SOFT_COUNTER_LIMIT=3

while [ "$SOFT_COUNTER" -lt "$SOFT_COUNTER_LIMIT" ]; do
    echo "Attaching hci0..."
    /usr/bin/hciattach /dev/ttyAMA0 bcm43xx 921600 noflow -

    echo "Bring hci0 up..."
    hciconfig hci0 up

    echo "Scan for devices..."
    if [ $(hcitool scan | wc -l) -le 1 ]; then
        FAILED=1
    else
        FAILED=0
    fi

    # Test result
    if [ $FAILED -eq 1 ]; then
        echo "Initialization failed."

        let SOFT_COUNTER=SOFT_COUNTER+1
        echo "Soft error counter: $SOFT_COUNTER/$SOFT_COUNTER_LIMIT"

        sleep $(shuf -i1-60 -n1)
    else
        echo "Initialization successful."
        break
    fi
done

# Primitive error handling
if [ $FAILED -eq 1 ]; then

    HARD_COUNTER_FILE=/tmp/restart_counter
    SLEEP=$(shuf -i1-300 -n1)

    if [ ! -f "$HARD_COUNTER_FILE" ]; then
        echo 1 > "$HARD_COUNTER_FILE"
        HARD_COUNTER=1
    else
        HARD_COUNTER="$(cat $HARD_COUNTER_FILE)"
        let HARD_COUNTER=$HARD_COUNTER+1
        echo $HARD_COUNTER > $HARD_COUNTER_FILE
    fi

    echo "Hard error counter: $HARD_COUNTER/5"
    echo "All tests failed. Taking hard action in $SLEEP seconds."
    sleep $SLEEP

    if [  $HARD_COUNTER -lt 5 ]; then
        # Resin restart command
        echo "Restarting container."
        curl -X POST --header "Content-Type:application/json" \
            "$RESIN_SUPERVISOR_ADDRESS/v1/restart?apikey=$RESIN_SUPERVISOR_API_KEY"
    else
        echo "Restarting device."
        # Resin reboot command
        curl -X POST --header "Content-Type:application/json" \
            "$RESIN_SUPERVISOR_ADDRESS/v1/reboot?apikey=$RESIN_SUPERVISOR_API_KEY"
    fi
fi

python manage.py migrate

/usr/local/bin/celery \
    -A collector \
    worker \
    -l info \
    --concurrency=2 \
    --beat
