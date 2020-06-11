# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from .models import Device, ScanRecord


class ScanRecordAdmin(admin.ModelAdmin):
    model = ScanRecord

    list_display = [
        'device',
        'timestamp',
        'rssi',
    ]

    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)


class DeviceAdmin(admin.ModelAdmin):
    model = Device

    list_display = [
        'device_address',
        'seen_last',
        'seen_first',
        'seen_counter',
        'device_manufacturer',
        'seen_within_geofence',
    ]

    ordering = ('-seen_last',)
    readonly_fields = (
        'device_type'
        'seen_first',
        'seen_last',
        'seen_counter',
        'device_manufacturer',
        'seen_within_geofence',
        'ignore',
        'device_address',
    )


admin.site.register(Device, DeviceAdmin)
admin.site.register(ScanRecord, ScanRecordAdmin)
