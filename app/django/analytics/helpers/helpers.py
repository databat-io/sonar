from datetime import datetime

def chart_format_day_str(datetime_value):
    return datetime.strptime(datetime_value, '%Y-%m-%dT%H:%M').strftime('%H:%M %p')


def chart_format_month_str(datetime_value):
    return datetime.strptime(datetime_value, '%Y-%m-%d').strftime('%b %d')