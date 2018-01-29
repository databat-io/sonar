# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils import timezone
from django.db import models


class Device(models.Model):
    device_address = models.CharField(max_length=60)
    device_type = models.CharField(max_length=200)
    seen_first = models.DateTimeField(auto_now_add=True)
    seen_last = models.DateTimeField(auto_now=True)
    seen_counter = models.PositiveIntegerField(default=1)
    ignore = models.BooleanField(default=False)

    def __str__(self):
        return self.device_address

    def seen_this_hour(self):
        return self.seen_last.hour == timezone.now().hour and self.seen_last.date() == timezone.now().date()

    def seen_today(self):
        return self.seen_last.date() == timezone.now().date()

    def seen_this_week(self):
        return self.seen_last.strftime('%W') == timezone.now().strftime('%W')


class ScanRecord(models.Model):
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        editable=False,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    rssi = models.IntegerField()

    def __str__(self):
        return str(self.rssi)
