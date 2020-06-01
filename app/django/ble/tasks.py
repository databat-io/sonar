from __future__ import absolute_import, unicode_literals
from ble.lib import ble_helper
from ble.models import Device
from celery import task
from django.conf import settings
from django.utils import timezone


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
    perform_scan = ble_helper.scan_for_btle_devices(timeout=timeout)

    if perform_scan:
        for device in ble_helper.scan_for_btle_devices(timeout=timeout):
            populate_device(device)
    else:
        print("Unable to scan for devices.")
