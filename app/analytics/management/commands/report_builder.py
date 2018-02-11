from analytics import tasks
from ble.models import ScanRecord
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone


def get_oldest_scan():
    return ScanRecord.objects.order_by('timestamp').first().timestamp


def populate_monthly_reports():
    pointer = get_oldest_scan()
    end = timezone.now()

    while pointer.strftime('%Y-%m') < end.strftime('%Y-%m'):
        date = pointer.strftime('%Y-%m')
        print('Processing {}'.format(date))
        tasks.ble_generate_monthly_report(date)
        pointer = pointer + timedelta(days=28)


def populate_daily_reports():
    pointer = get_oldest_scan()
    end = timezone.now()

    while pointer.date() < end.date():
        date = pointer.strftime('%Y-%m-%d')
        print('Processing {}'.format(date))
        tasks.ble_generate_daily_report(date)
        pointer = pointer + timedelta(days=1)


def populate_hourly_reports():
    pointer = get_oldest_scan()
    end = timezone.now()

    while pointer.strftime('%Y-%m-%dT%H:00') < end.strftime('%Y-%m-%dT%H:00'):
        date = pointer.strftime('%Y-%m-%dT%H:00')
        print('Processing {}'.format(date))
        tasks.ble_generate_hourly_report(date)
        pointer = pointer + timedelta(hours=1)


class Command(BaseCommand):
    help = 'Resolve.'

    def handle(self, *args, **options):
        populate_monthly_reports()
        populate_daily_reports()
        populate_hourly_reports()
