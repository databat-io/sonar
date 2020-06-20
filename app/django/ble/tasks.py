from __future__ import absolute_import, unicode_literals
from ble.lib import ble_helper
from ble.models import Device
from bluepy.btle import ScanEntry
from celery import task
from django.conf import settings
from django.utils import timezone
from collector.lib import redis_helper
import json
import requests

r = redis_helper.redis_connection(decode=True)

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
    """
    Populates the dataset. If Databat is enabled,
    also submit the payload to Databat's backend.
    """

    payload = {
        'timestamp': timezone.now(),
        'device_type': device.addrType,
        'rssi': device.rssi,
        'seen_counter': 1,
        'capture_device': settings.DEVICE_ID,
    }


    obj, created = Device.objects.get_or_create(
            device_address=device.addr,
            device_type=device.addrType,
    )

    if device.getValue(ScanEntry.MANUFACTURER):
        manufacturer = ble_helper.lookup_bluetooth_manufacturer(
            device.getValueText(ScanEntry.MANUFACTURER)
        )
        obj.device_manufacturer = manufacturer
        payload['device_manufacturer'] = device.getValueText(ScanEntry.MANUFACTURER)

        obj.device_manufacturer_string_raw = device.getValueText(ScanEntry.MANUFACTURER)
        payload['device_manufacturer_string_raw'] = device.getValueText(ScanEntry.MANUFACTURER)

    if not created:
        obj.seen_counter = obj.seen_counter + 1
        payload['seen_counter'] = obj.seen_counter

    if int(device.rssi) < settings.SENSITIVITY:
        obj.seen_within_geofence = True

    obj.ignore = obj.seen_counter > settings.DEVICE_IGNORE_THRESHOLD

    device_fingerprint = ble_helper.build_device_fingerprint(device)
    obj.device_fingerprint = device_fingerprint
    payload['device_fingerprint'] = device_fingerprint

    obj.seen_last = timezone.now()
    obj.scanrecord_set.create(rssi=device.rssi)
    obj.save()

    return payload

@task
def submit_to_databat(payload):
    submit_payload = requests.post(
        'https://us-central1-databat.cloudfunctions.net/post-record',
        params = {'api_token': settings.DATABAT_API_TOKEN},
        data=json.dumps(payload)
    )
    return submit_payload

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
    result = []
    devices_within_geofence = 0
    if perform_scan:
        for device in ble_helper.scan_for_btle_devices(timeout=timeout):
            result.append(
                populate_device(device)
            )

            if device.rssi < settings.SENSITIVITY:
                devices_within_geofence = devices_within_geofence + 1

        return('Successfully scanned. Found {} devices within the geofence ({} in total).'.format(
            devices_within_geofence,
            len(perform_scan))
        )
        if settings.DATABAT_API_TOKEN:
            submit_to_databat.delay(payload)
    else:
        return('Unable to scan for devices.')
