from __future__ import absolute_import, unicode_literals
from ble.models import ScanRecord
from analytics.models import BleReport
from datetime import datetime, timedelta
from celery import task
from django.utils import timezone
import pytz


@task
def ble_generate_hourly_report(date=None):
    """
    Takes the input in the form of YYYY-MM-DDTHH:MM
    as per ISO 8601. If no input is specified,
    the last hour will be used
    """

    # We use this for automated reports from celery
    if not date:
        last_hour = timezone.now() - timedelta(hours=1)
        date = last_hour.strftime('%Y-%m-%dT%H:00')

    if BleReport.objects.filter(period=date).first():
        print('Report already exist.')
        return

    tz = timezone.now().tzname()
    datetime_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M')
    datetime_obj_local = datetime_obj.replace(tzinfo=pytz.timezone(tz))

    devices = set()
    for d in ScanRecord.objects.filter(
        timestamp__date=datetime_obj_local.date(),
        timestamp__hour=datetime_obj_local.hour
    ):
        devices.add(d.device.device_address)

    return BleReport.objects.create(
        report_type='H',
        count=len(devices),
        timezone=tz,
        period=date,
    )


@task
def ble_generate_daily_report(date=None):
    """
    Takes the input in the form YYYY-MM-DD
    """

    # We use this for automated reports from celery
    if not date:
        yesterday = timezone.now() - timedelta(days=1)
        date = yesterday.strftime('%Y-%m-%d')

    if BleReport.objects.filter(period=date).first():
        print('Report already exist.')
        return

    tz = timezone.now().tzname()
    datetime_obj = datetime.strptime(date, '%Y-%m-%d')
    datetime_obj_local = datetime_obj.replace(tzinfo=pytz.timezone(tz))

    devices = set()
    for d in ScanRecord.objects.filter(
        timestamp__date=datetime_obj_local.date()
    ):
        devices.add(d.device.device_address)

    return BleReport.objects.create(
        report_type='D',
        count=len(devices),
        timezone=tz,
        period=date,
    )


@task
def ble_generate_monthly_report(date=None):
    """
    Takes the input in the form YYYY-MM
    """

    # We use this for automated reports from celery
    if not date:
        last_month = timezone.now() - timedelta(months=1)
        date = last_month.strftime('%Y-%m')

    if BleReport.objects.filter(period=date).first():
        print('Report already exist.')
        return

    tz = timezone.now().tzname()
    datetime_obj = datetime.strptime(date, '%Y-%m')
    datetime_obj_local = datetime_obj.replace(tzinfo=pytz.timezone(tz))
    devices = set()

    for d in ScanRecord.objects.filter(
        timestamp__year=datetime_obj_local.year,
        timestamp__month=datetime_obj_local.month,
    ):
        devices.add(d.device.device_address)

    return BleReport.objects.create(
        report_type='M',
        count=len(devices),
        timezone=tz,
        period=date,
    )
