import json

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User, AnonymousUser
from main import models
from datetime import datetime, timedelta
from main.data import checkMeetingData

from main.helpers import getCalendar, getUsers

def calendardemo(request):
	template = loader.get_template('main/calendardemo.html')
	return HttpResponse(template.render({}, request))

def login(request):
	template = loader.get_template('main/login.html')
	return HttpResponse(template.render({}, request))

@login_required()
def index(request):
	template = loader.get_template('main/index.html')

	content = {}
	user = None
	if request.user.is_authenticated():
		user = request.user
		content['email'] = user.email
		content['loggedIn'] = True
		content['isSuperUser'] = user.is_superuser

		meetings, rooms = getCalendar(request)
		content['meetings'] = meetings
		content['rooms'] = rooms

		content['users'] = getUsers(request)
	else:
		content['loggedIn'] = False
	return HttpResponse(template.render(content, request))
