from __future__ import absolute_import, unicode_literals
from ble.models import ScanRecord
from analytics.models import Report
from datetime import timedelta
from django.utils import timezone
from celery import task


@task
def generate_hourly_report(offset=0):
    range_end = timezone.now().replace(
        minute=0,
        second=0,
        microsecond=0
    ) - timedelta(hours=offset)
    range_start = range_end - timedelta(hours=1 + offset)
    devices = set()

    for d in ScanRecord.objects.filter(
        timestamp__range=[range_start, range_end]
    ):
        devices.add(d.device.device_address)

    return Report.objects.create(
        report_type='H',
        count=len(devices),
        range_start=range_start,
        range_end=range_end,
    )
