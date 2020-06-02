from bluepy.btle import Scanner, DefaultDelegate, BTLEManagementError
from django.conf import settings
import redis

r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DATABASE
)


def scan_for_btle_devices(timeout=30):
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

    scanner = Scanner().withDelegate(ScanDelegate())

    try:
        with r.lock('ble-scan-lock', blocking_timeout=timeout+2) as lock:
            return(scanner.scan(float(timeout)))
    except redis.exceptions.LockError:
        print("Failed to acquire lock")
        return
    except BTLEManagementError:
        print("Got BTLEManagementError. This is probably due to two parallel sessions.")
        return
