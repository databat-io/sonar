#!/bin/bash

# Clean up
rmmod hci_uart btbcm bluetooth xt_tcpudp veth

# Start up
hciattach /dev/ttyAMA0 bcm43xx 921600 noflow -
hciconfig hci0 up
