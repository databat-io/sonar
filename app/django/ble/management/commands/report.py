from django.core.management.base import BaseCommand
from ble.models import Device
from django.utils import timezone


def get_hourly():
    return Device.objects.filter(
        seen_last__date=timezone.now().date(),
        seen_last__hour=timezone.now().hour
    ).count()


def get_daily():
    return Device.objects.filter(
        seen_last__date=timezone.now().date()
    ).count()


def get_weekly():
    return Device.objects.filter(
        seen_last__week=timezone.now().isocalendar()[1]
    ).count()


class Command(BaseCommand):
    help = 'Report BLE devices found.'

    def handle(self, *args, **options):
        print('Hourly: {}'.format(get_hourly()))
        print(' Daily: {}'.format(get_daily()))
        print('  Week: {}'.format(get_weekly()))
