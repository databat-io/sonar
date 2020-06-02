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

    try:
        with r.lock('ble-scan-lock', blocking_timeout=timeout+5) as lock:
            scanner = Scanner().withDelegate(ScanDelegate())
            print('got here')
            scan_result = scanner.scan(float(timeout))
            print('got here too')
            return(scan_result)
    except redis.exceptions.LockError:
        print("Failed to acquire lock")
        return
    except BTLEManagementError:
        print("Got BTLEManagementError. This is probably due to two parallel sessions.")
        return
