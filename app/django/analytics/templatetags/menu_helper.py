from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def is_sidebar_active(page_title, menu_item):
    if page_title in menu_item:
        return 'active'
    else:
        return 'inactive'
