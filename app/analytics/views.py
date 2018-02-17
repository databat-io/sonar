# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from chartit import DataPool, Chart
from django.shortcuts import render, render_to_response, reverse, redirect
from .helpers.helpers import chart_format_day_str, chart_format_month_str
from .models import BleReport
from .forms import DayReportForm, MonthReportForm
from datetime import datetime


def index(request, *args, **kwargs):

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
        'min_day': min_day,
        'max_day': max_day,
        'enabled_days_list': enabled_days_list,
        'day_form': day_form,
        'month_form': month_form,
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

    return render_to_response(
        'analytics/graph.html',
        context={'chart': cht, 'year': year, 'month': month, 'page_title': page_title}
    )


def login_demo_view(request, *args, **kwargs):
    page_title = "Login page"

    return render_to_response(
        'analytics/login.html', context={}
    )