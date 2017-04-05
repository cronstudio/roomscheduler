from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.conf.urls import include, url

from . import views
from main.api import urlpatterns as apipatterns

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login$', views.login, name='login'),
    url(r'^api/', include(apipatterns)),

    url(r'^calendar$', views.calendar, name='calendar'),
    url(r'^users$', views.users, name='users'),
    url(r'^resources$', views.resources, name='resources'),

    url(r'^accessRevoked$', views.accessRevoked, name='accessRevoked'),
    url(r'^', views.handler404, name='handler404'),
]
