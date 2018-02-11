from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$', views.day_view, name='day_view'),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', views.month_view, name='month_view')
]
