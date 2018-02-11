# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from .models import BleReport


class BleReportAdmin(admin.ModelAdmin):
    model = BleReport

    list_display = [
        'count',
        'period',
        'report_type',
        'timestamp',
    ]

    list_filter = (
        'report_type',
    )

    ordering = (
        'period',
    )

    readonly_fields = (
        'period',
        'timestamp',
        'timezone',
        'count'
    )


admin.site.register(BleReport, BleReportAdmin)
