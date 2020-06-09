from __future__ import absolute_import, unicode_literals
from ble.lib import ble_helper
from ble.models import Device
from celery import task
from django.conf import settings
from django.utils import timezone
import requests
import redis

r = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DATABASE
)


def get_error_counter():
    """
    Return error counter.
    If undefined, return 0.
    """
    counter = r.get('btle-error')
    if counter:
        return int(counter)
    return 0


def populate_device(device):

    obj, created = Device.objects.get_or_create(
            device_address=device.addr,
            device_type=device.addrType,
    )

    if not created:
        obj.seen_counter = obj.seen_counter + 1

    if int(device.rssi) < settings.SENSITIVITY:
        obj.seen_within_geofence = True

    if obj.seen_counter > settings.DEVICE_IGNORE_THRESHOLD:
        obj.ignore_list = True

    obj.seen_last = timezone.now()
    obj.scanrecord_set.create(rssi=device.rssi)
    obj.save()


@task
def scan(timeout=30):

    if get_error_counter() > 20:
        print('Hit BTLEManagementError threshold. Rebooting.')
        if settings.BALENA:
            perform_reboot = requests.post(
                '{}/v1/reboot'.format(settings.BALENA_SUPERVISOR_ADDRESS),
                params = {'apikey': settings.BALENA_SUPERVISOR_API_KEY}
            )
            return perform_reboot
        else:
            print('Reboot for non-Balena is not implemented yet.')

    perform_scan = ble_helper.scan_for_btle_devices(timeout=timeout)
    devices_within_geofence = 0
    if perform_scan:
        for device in ble_helper.scan_for_btle_devices(timeout=timeout):
            populate_device(device)
            if device.rssi < settings.SENSITIVITY:
                devices_within_geofence = within_geofence + 1
        return('Successfully scanned. Found {} devices within the geofence ({} in total).'.format(
            devices_within_geofence,
            len(perform_scan))
        )
    else:
        return('Unable to scan for devices.')
