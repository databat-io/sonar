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


def populate_device(device):

    obj, created = Device.objects.get_or_create(
            device_address=device.addr,
            device_type=device.addrType,
    )

    if not created:
        obj.seen_counter = obj.seen_counter + 1

    if obj.seen_counter > settings.DEVICE_IGNORE_THRESHOLD:
        obj.ignore_list = True

    obj.seen_last = timezone.now()
    obj.scanrecord_set.create(rssi=device.rssi)
    obj.save()


@task
def scan(timeout=30):

    if r.get('btle_error') > 20:
        print('Hit BTLEManagementError threashold. Rebooting.')
        perform_reboot = requests.post(
            '{}/v1/reboot'.format(settings.BALENA_SUPERVISOR_ADDRESS),
            params = {'apikey': settings.BALENA_SUPERVISOR_API_KEY}
        )
        return perform_reboot

    perform_scan = ble_helper.scan_for_btle_devices(timeout=timeout)
    if perform_scan:
        for device in ble_helper.scan_for_btle_devices(timeout=timeout):
            populate_device(device)
        return('Successfully scanned.')
    else:
        return('Unable to scan for devices.')
