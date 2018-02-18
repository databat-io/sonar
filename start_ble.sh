#!/bin/bash

# Only bring up interface if it is absent
if [ -z $(hciconfig) ]; then
    hciattach /dev/ttyAMA0 bcm43xx 921600 noflow -
    hciconfig hci0 up
fi

SOFT_COUNTER=0
SOFT_COUNTER_LIMIT=3
while [ "$SOFT_COUNTER" -lt "$SOFT_COUNTER_LIMIT" ]; do
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
