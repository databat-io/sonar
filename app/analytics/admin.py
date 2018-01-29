# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from .models import Report


class ReportAdmin(admin.ModelAdmin):
    model = Report

    list_display = [
        'count',
        'range_start',
        'range_end',
        'report_type',
        'timestamp',
    ]

    ordering = (
        'timestamp',
    )
    readonly_fields = (
        'range_end',
        'range_start',
        'timestamp',
    )


admin.site.register(Report, ReportAdmin)
