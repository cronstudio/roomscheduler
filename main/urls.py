from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^calendardemo', views.calendardemo, name='calendardemo'),
    url(r'^auth', views.authForm, name='authForm'),
    url(r'^rooms', views.rooms, name='rooms'),
    url(r'^calendar', views.calendar, name='calendar'),
	url(r'^createMeeting', views.createMeeting, name='createMeeting'),
	url(r'^editMeeting', views.editMeeting, name='editMeeting'),
	url(r'^deleteMeeting', views.deleteMeeting, name='deleteMeeting'),
	url(r'^requiresLogin', views.requiresLogin, name='requiresLogin'),
]
