# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from .models import BleReport


def index(request):
    month_views_available = BleReport.objects.filter(
        report_type='M'
    ).order_by('period')
    day_views_available = BleReport.objects.filter(
        report_type='D'
    ).order_by('period')
    context = {
        'monthly_reports': month_views_available,
        'daily_reports': day_views_available,
    }
    return render(request, 'analytics/index.html', context)


def day_view(request, year, month, day):
    hourly_reports = BleReport.objects.filter(
            report_type='H',
            period__startswith='{}-{}-{}'.format(year, month, day),
    ).order_by('period')
    context = {
        'hourly_reports': hourly_reports,
    }
    return render(request, 'analytics/day_view.html', context)


def month_view(request, year, month):
    daily_reports = BleReport.objects.filter(
            report_type='D',
            period__startswith='{}-{}'.format(year, month),
    ).order_by('period')
    context = {
        'daily_reports': daily_reports,
    }
    return render(request, 'analytics/month_view.html', context)
