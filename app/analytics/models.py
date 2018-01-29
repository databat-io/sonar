# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models

REPORT_TYPE = (
    ('H', 'Hour'),
    ('D', 'Day'),
    ('W', 'Week'),
    ('M', 'Month'),
)


class Report(models.Model):
    report_type = models.CharField(
        max_length=1,
        choices=REPORT_TYPE,
    )
    range_start = models.DateTimeField()
    range_end = models.DateTimeField()
    count = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
