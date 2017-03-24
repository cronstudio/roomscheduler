from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.conf.urls import include, url

from . import views
from main.api import urlpatterns as apipatterns

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login', views.login, name='login'),
    url(r'^calendardemo', views.calendardemo, name='calendardemo'),
    url(r'^api/', include(apipatterns)),
]
