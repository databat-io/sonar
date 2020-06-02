from bluepy.btle import Scanner, DefaultDelegate, BTLEManagementError
from django.conf import settings
import redis

LOCK_NAME = 'ble-lock'
r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DATABASE
)


def set_lock(timeout):
    if r.get(LOCK_NAME):
        return False
    else:
        r.set(LOCK_NAME, 1)
        r.expire(LOCK_NAME, timeout)
        return True

def delete_lock():
    r.delete(LOCK_NAME)


def scan_for_btle_devices(timeout=30):
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

    try:
        if set_lock(timeout+5):
            scanner = Scanner().withDelegate(ScanDelegate())
            print('got here')
            scan_result = scanner.scan(float(timeout))
            print('got here too')
            delete_lock()
            return(scan_result)
        else:
            print("Failed to acquire lock")
            return
    except BTLEManagementError:
        print("Got BTLEManagementError. This is probably due to two parallel sessions.")
        return
