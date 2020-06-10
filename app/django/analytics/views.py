# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .forms import DayReportForm, MonthReportForm
from .helpers.helpers import chart_format_day_str, chart_format_month_str
from .models import BleReport
from ble.models import ScanRecord, Device
from chartit import DataPool, Chart
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render, render_to_response, reverse, redirect
from django.utils import timezone
import redis

r = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DATABASE
)


def get_visitors_today():
    current_time = timezone.now()
    if not r.get('visitors-today'):
        visitors_today = ScanRecord.objects.filter(
            timestamp__date=current_time.date(),
            rssi__lte=settings.SENSITIVITY
        ).count()
        r.set('visitors-today', visitors_today)
        r.expire('visitors-today', 60*10)
        return visitors_today
    else:
        return int(r.get('visitors-today'))


def get_visitors_this_hour():
    current_time = timezone.now()

    if not r.get('visitors-this-hour'):
        visitors_this_hour = ScanRecord.objects.filter(
            timestamp__date=current_time.date(),
            timestamp__hour=current_time.hour,
            rssi__lte=settings.SENSITIVITY
        ).count()
        r.set('visitors-this-hour', visitors_this_hour)
        r.expire('visitors-this-hour', 60*5)
        return visitors_this_hour
    else:
        return int(r.get('visitors-this-hour'))


def get_returning_visitors(days=30):
    current_time = timezone.now()
    redis_key = 'returning-visitors-{}'.format(days)

    if not r.get(redis_key):
        returning_visitors = Device.objects.filter(
            ignore=False,
            seen_within_geofence=True,
            seen_last__gte=current_time - timedelta(days=1),
            seen_first__gte=current_time - timedelta(days=days),
            seen_first__lte=current_time - timedelta(days=1)
        ).count()
        r.set(redis_key, returning_visitors)
        r.expire(redis_key, 60*15)
        return return_visitors
    else:
        return int(r.get(redis_key))



def dashboard(request, *args, **kwargs):
    page_title = "Dashboard"

    context = {
        'page_title': page_title,
        'visitors_this_hour': get_visitors_this_hour(),
        'visitors_today': get_visitors_today(),
        'returning_visitors_30_days': get_returning_visitors(days=30),
        'returning_visitors_60_days': get_returning_visitors(days=60),
        'returning_visitors_180_days': get_returning_visitors(days=180),
    }
    return render(request, 'analytics/dashboard.html', context)


def report(request, *args, **kwargs):
    page_title = "Report"

    day_periods = BleReport.objects.filter(
        report_type='D'
    ).values_list('period', flat=True).order_by('period')

    # Create lists of available days and pass to the view as context
    enabled_days_list = []
    for day_period in day_periods:
        if day_period not in enabled_days_list and len(day_period) == 10:
            enabled_days_list.append(day_period)

    # Get the min day and max day bounds for the day report datepicker
    min_day = None
    max_day = None
    if day_periods:
        sorted(day_periods, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
        min_day = day_periods[0]
        max_day = day_periods[len(day_periods)-1]

    day_form = DayReportForm()
    month_form = MonthReportForm()

    if request.method == "POST":

        day_report_submitted = request.POST.get('day_report', None)
        month_report_submitted = request.POST.get('month_report', None)

        if day_report_submitted:
            day_form = DayReportForm(request.POST)

            if day_form.is_valid():
                return redirect(reverse('day_view', kwargs=day_form.cleaned_data['day_selected']))
            else:
                pass # And re-render the template with form errors (done below)

        elif month_report_submitted:
            month_form = MonthReportForm(request.POST)

            if month_form.is_valid():
                return redirect(reverse('month_view', kwargs=month_form.cleaned_data['month_selected']))
            else:
                pass # And re-render the template with form errors (done below)

    context = {
        'page_title': page_title,
        'min_day': min_day,
        'max_day': max_day,
        'enabled_days_list': enabled_days_list,
        'day_form': day_form,
        'month_form': month_form,
    }
    return render(request, 'analytics/report.html', context)


def day_view(request, year, month, day):
    page_title = "Report: Day view"

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
        series_options=[
            {
                'options': {
                    'type': 'line',
                    'stacking': False
                },
                'terms': {
                    'period': ['count']
                }
            }
        ],

        chart_options={
            'legend': {
                'enabled': False
            },
            'title': {
                'text': 'none',
                'style': {
                    'display': 'none',
                }
            },
            'credits': False,
            'xAxis': {
                'title': {
                    'text': 'none',
                    'style': {
                        'display': 'none'
                    }
                },
                'labels': {
                    'style': {
                        'fontFamily': '"Open Sans", sans-serif',
                        'color': '#7e8e9f'
                    }
                },
                'dateTimeLabelFormats': {
                    'hour': '%H:%M',
                },
                'tickInterval': 2,
            },
            'yAxis': {
                'min': 0,
                'title': {
                    'text': 'Devices discovered',
                    'style': {
                        'fontFamily': '"Open Sans", sans-serif',
                        'color': '#7e8e9f',
                        'font-weight': 'normal'
                    }
                },
                'labels': {
                    'style': {
                        'fontFamily': '"Open Sans", sans-serif',
                        'color': '#7e8e9f'
                    }
                },
                'gridLineColor': '#e9ecef'
            },
            'plotOptions': {
                'series': {
                    'color': '#85CE36'
                }
            }
        },
        x_sortf_mapf_mts=(None, chart_format_day_str, False)
    )

    context = {
        'chart': cht,
        'year': year,
        'month': month,
        'day': day,
        'page_title': page_title
    }

    return render_to_response(
        'analytics/graph.html',
        context=context
    )


def month_view(request, year, month):
    page_title = "Report: Month view"

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
            'legend': {
                'enabled': False
            },
            'title': {
                'text': 'Devices discovered on an daily basis.',
                'style': {
                    'display': 'none',
                }
            },
            'credits': False,
            'xAxis': {
                'title': {
                    'text': 'none',
                    'style': {
                        'display': 'none'
                    }
                },
                'labels': {
                    'style': {
                        'fontFamily': '"Open Sans", sans-serif',
                        'color': '#7e8e9f'
                    }
                },
                'dateTimeLabelFormats': {
                    'hour': '%H:%M',
                },
                'tickInterval': 3,
            },
            'yAxis': {
                'min': 0,
                'title': {
                    'text': 'Devices discovered',
                    'style': {
                        'fontFamily': '"Open Sans", sans-serif',
                        'color': '#7e8e9f',
                        'font-weight': 'normal'
                    }
                },
                'labels': {
                    'style': {
                        'fontFamily': '"Open Sans", sans-serif',
                        'color': '#7e8e9f'
                    }
                },
                'gridLineColor': '#e9ecef'
            },
            'plotOptions': {
                'series': {
                    'color': '#85CE36'
                }
            }
        },
        x_sortf_mapf_mts=(None, chart_format_month_str, False)
    )
    context = {
        'chart': cht,
        'year': year,
        'month': month,
        'page_title': page_title
    }

    return render_to_response(
        'analytics/graph.html',
        context=context
    )


def login_demo_view(request, *args, **kwargs):
    page_title = "Login page"

    return render_to_response(
        'analytics/login.html', context={}
    )
