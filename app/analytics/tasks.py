from __future__ import absolute_import, unicode_literals
from analytics.models import BleReport
from ble.models import ScanRecord
from celery import task
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from mixpanel import Mixpanel, MixpanelException
import pytz


def ping_mixpanel():
    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    try:
        mp.track(settings.DEVICE_ID, 'ping')
    except MixpanelException:
        pass
    except AttributeError:
        pass


@task
def ble_generate_hourly_report(date=None):
    """
    Takes the input in the form of YYYY-MM-DDTHH:MM
    as per ISO 8601. If no input is specified,
    the last hour will be used
    """

    ping_mixpanel()

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
        # Ugly workaround to get last month
        # https://stackoverflow.com/questions/9724906/python-date-of-the-previous-month
        today = timezone.now()
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
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


@task
def ble_fill_report_backlog(report_type):

    if report_type == 'H':
        date_format = '%Y-%m-%dT%H:%M'
    elif report_type == 'D':
        date_format = '%Y-%m-%d'
    elif report_type == 'M':
        date_format = '%Y-%m'
    else:
        return 'No report type selected'

    tz = timezone.now().tzname()
    oldest_scan_record = ScanRecord.objects.filter().order_by(
        'timestamp'
    )[0].timestamp.replace(tzinfo=pytz.timezone(tz))

    newest_scan_record = ScanRecord.objects.filter().order_by(
        '-timestamp'
    )[0].timestamp.replace(tzinfo=pytz.timezone(tz))

    record_to_check = oldest_scan_record + timedelta(hours=1)

    while record_to_check < newest_scan_record:
        if report_type == 'H':
            period = record_to_check.strftime('%Y-%m-%dT%H:00')
            if not BleReport.objects.filter(period=period):
                return ble_generate_hourly_report(date=period)
            else:
                record_to_check = record_to_check + timedelta(hours=1)
        elif report_type == 'D':
            period = record_to_check.strftime(date_format)
            if not BleReport.objects.filter(period=period):
                return ble_generate_daily_report(date=period)
            else:
                record_to_check = record_to_check + timedelta(days=1)
        elif report_type == 'M':
            period = record_to_check.strftime(date_format)
            if not BleReport.objects.filter(period=period):
                return ble_generate_monthly_report(date=period)
            else:
                record_to_check = record_to_check + timedelta(months=1)
    return 'No more records to populate.'
