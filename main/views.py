import json

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, JsonResponse
from django.template import loader, RequestContext
from django.contrib.auth.models import User, AnonymousUser
from main import models
from datetime import datetime, timedelta
from main.data import checkMeetingData

from main.helpers import getCalendar, getUsers
from django.contrib.auth.decorators import user_passes_test

def login(request):
	template = loader.get_template('main/login.html')
	return HttpResponse(template.render({}, request))

@login_required()
def index(request, view="calendar"):
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

		content['view'] = view
	else:
		content['loggedIn'] = False
	return HttpResponse(template.render(content, request))

@login_required()
def calendar(request):
	return index(request, "calendar")

@user_passes_test(lambda u: u.is_superuser, login_url="/accessRevoked")
def users(request):
	return index(request, "users")

@user_passes_test(lambda u: u.is_superuser, login_url="/accessRevoked")
def resources(request):
	return index(request, "rooms")

def accessRevoked(request):
	template = loader.get_template('main/accessRevoked.html')
	return HttpResponse(template.render({}, request))


def handler404(request):
    template = loader.get_template('main/404.html')
    return HttpResponse(content=template.render({}, request), status=404)
