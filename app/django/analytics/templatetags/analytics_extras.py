from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def get_time(value):
    return value.split('T')[1]


@register.filter
@stringfilter
def convert_to_url(value):
    return value.replace('-', '/')
