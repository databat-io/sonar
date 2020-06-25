import re
import os


def get_serial():
    """
    Return serial number of the Raspberry Pi,
    or False if not a Raspberry Pi
    """
    if not os.path.isfile('/proc/cpuinfo'):
        return False

    with open('/proc/cpuinfo') as f:
        serial = re.search(r"(?<=\nSerial)[ |:|\t]*(\w+)", f.read())

    return serial.group(1) if serial else False
