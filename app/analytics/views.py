# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from chartit import DataPool, Chart
from datetime import datetime

from django.shortcuts import render, render_to_response
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
    page_title = "Day view"

    hourly_reports = BleReport.objects.filter(
            report_type='H',
            period__startswith='{}-{}-{}'.format(year, month, day),
    ).order_by('period')

    report_data = DataPool(
            series=[
                {
                    'options': {
                        'source': hourly_reports,
                    },
                    'terms': [
                        'period',
                        'count'
                    ]
                }
            ]
    )


    cht = Chart(
        datasource=report_data,
        series_options=[{
            'options': {
                'type': 'line',
                'stacking': False
            },
            'terms': {
                'period': ['count']
                }
            }],
        chart_options={
            'title': {
                'text': 'Devices discovered on an hourly basis.'
            },
            'xAxis': {
                'title': {
                    'text': 'Hourly number'
                },
                'type': 'datetime',
            },
            'yAxis': {
                'min': 0
            }
        }
    )

    return render_to_response(
        'analytics/graph.html',
        context={'chart': cht, 'year': year, 'month': month, 'day': day, 'page_title': page_title}
    )


def month_view(request, year, month):
    page_title = "Month view"

    daily_reports = BleReport.objects.filter(
            report_type='D',
            period__startswith='{}-{}'.format(year, month),
    ).order_by('period')

    report_data = DataPool(
           series=[
               {'options': {
                   'source': daily_reports
               },
                   'terms': [
                       'period',
                       'count']}
             ])

    cht = Chart(
        datasource=report_data,
        series_options=[{
            'options': {
                'type': 'line',
                'stacking': False
            },
            'terms': {
                'period': ['count']
                }
            }],
        chart_options={
            'title': {
                'text': 'Devices discovered on an daily basis.'
            },
            'xAxis': {
                'title': {
                    'text': 'Daily number'
                }
            }
        }
    )

    return render_to_response(
        'analytics/graph.html',
        context={'chart': cht, 'year': year, 'month': month, 'page_title': page_title}
    )
