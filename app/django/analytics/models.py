# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models

REPORT_TYPE = (
    ('H', 'Hour'),
    ('D', 'Day'),
    ('W', 'Week'),
    ('M', 'Month'),
)


class BleReport(models.Model):
    class Meta:
        managed = True

    report_type = models.CharField(
        max_length=1,
        choices=REPORT_TYPE,
        editable=False,
    )
    timezone = models.CharField(max_length=60, editable=False)
    period = models.CharField(max_length=60, primary_key=True)
    count = models.PositiveIntegerField(editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return self.period
