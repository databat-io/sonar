from bluepy.btle import Scanner, DefaultDelegate, BTLEManagementError
from django.conf import settings
import redis

LOCK_NAME = 'btle-lock'
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


def log_btle_error():
    btle_error_key = 'btle-error'
    btle_error_key_ttl = 3600

    if r.get(btle_error_key):
        r.incr(btle_error_key)
        r.expire(btle_error_key, btle_error_key_ttl)
    else:
        r.set(btle_error_key, 1)
        r.expire(btle_error_key, btle_error_key_ttl)


def scan_for_btle_devices(timeout=30):
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

    try:
        if set_lock(timeout+5):
            scanner = Scanner().withDelegate(ScanDelegate())
            scan_result = scanner.scan(float(timeout), passive=True)
            delete_lock()
            return(scan_result)
        else:
            print('Failed to acquire lock.')
            return
    except BTLEManagementError:
        log_btle_error()
        print('Got BTLEManagementError. Failure counter at {}.'.format(r.get('btle-error')))
        return
