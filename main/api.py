import json

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User, AnonymousUser
from main import models
from datetime import datetime, timedelta
from main.data import checkMeetingData

from django.conf.urls import include, url
from main.helpers import *

def calendar(request):
	if request.user.is_authenticated():
		meetings, rooms = getCalendar(request)

		return JsonResponse({'result': 'Success', 'meetings': meetings, 'rooms': rooms})
	return JsonResponse({'result': 'Failed'})

def authForm(request):
	if request.method == 'POST':
		if request.POST['action'] == 'login':
			return login(request)
		elif request.POST['action'] == 'register':
			return register(request)
		elif request.POST['action'] == 'logout':
			return logout(request)

def rooms(request):
	if request.method == 'GET':
		if request.user.is_authenticated():
			data = models.Room.objects.all().values('id', 'name')
			return JsonResponse({'result': 'Success', 'rooms': list(data)})
		else:
			return JsonResponse({'result': 'Failed', 'message': 'User not logged in'})
	else:
		return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected GET, received ' + request.method})


@login_required(redirect_field_name="requiresLogin")
def createMeeting(request):
	if request.method == 'POST':
		data = request.POST
		start, duration = parseMeetingTime(data)
		
		meeting = models.Meeting(user=request.user, description=data['description'], start=start, duration=duration, room=models.Room.objects.get(id=int(data['room']) ) )
		result, message = checkMeetingData(meeting);
		if not result:
			return JsonResponse({'result': 'Failed', 'message': message})
		else:
			meeting.save()
			return JsonResponse({'result': 'Success'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def editMeeting(request):
	print("Is super user?", request.user.is_superuser)
	# TODO: check owner
	if request.method == 'POST':
		data = request.POST
		start, duration = parseMeetingTime(data)
		
		meeting = models.Meeting.objects.get(id=data['id'])
		meeting.description = data['description']
		meeting.start = start
		meeting.duration = duration
		meeting.room = models.Room.objects.get(id=int(data['room']) )
		
		result, message = checkMeetingData(meeting);
		if not result:
			return JsonResponse({'result': 'Failed', 'message': message})
		else:
			meeting.save()
			return JsonResponse({'result': 'Success'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def deleteMeeting(request):
	if request.method == 'POST':
		data = request.POST
		
		try:
			meeting = models.Meeting.objects.get(id=data['id'])
			if meeting.user.id != request.user.id:
				return JsonResponse({'result': 'Failed', 'message': 'Cannot delete meeting created by someone else'})
			meeting.delete()
			return JsonResponse({'result': 'Success'})
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': 'Invalid meeting id'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})


def login(request):
	email = request.POST['email']
	password = request.POST['password']
	found = None
	l = User.objects.filter(email=email)
	if len(l) > 0:
		found = User.objects.get(email=email)
	print(email, password)
	user = auth.authenticate(username=email, password=password)

	response_data = {}
	if user is not None:
		auth.login(request, user)
		response_data['result'] = 'Success'
		response_data['message'] = '';
	else:
		if found != None and found.is_active == False:
			response_data['result'] = 'Failed'
			response_data['message'] = 'Account must be activated by an admin'
		elif found != None:
			response_data['result'] = 'Failed'
			response_data['message'] = 'Wrong password!'
		else:
			response_data['result'] = 'Failed'
			response_data['message'] = 'No account found for this username'
	
	return JsonResponse(response_data)

def register(request):
	email = request.POST['email']
	password = request.POST['password']
	response_data = {}

	if User.objects.filter(username=email).exists():
		success = False
		response_data['result'] = 'Failed'
		response_data['message'] = 'This username is already in use'
	else:
		user = User.objects.create_user(username=email, email=email, password=password)
		user.is_active = False
		user.save()
		response_data['result'] = 'Success'
		response_data['message'] = 'Account created'

	return JsonResponse(response_data)

def logout(request):
	auth.logout(request)
	
	return JsonResponse({'result': 'Success', 'message': 'Logged out successfully'})

def requiresLogin(request):
	return JsonResponse({'result': 'Failed', 'message': 'This action requires login'})

def editUser(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = request.POST
		try:
			user = User.objects.get(id=data['id'])
			user.username = user.email = data['email']
			user.entity.name = data['entity']
			user.first_name = data['name']
			user.save()
			return JsonResponse({'result': 'Success', 'message': ''})
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': 'User id not found'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

def addUser(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = request.POST
		
		user = User()
		user.email = user.username = data['email']
		user.entity = models.Entity(name=data['entity'])
		user.first_name = data['name']
		user.save()
		return JsonResponse({'result': 'Success', 'message': '', 'data': {'id': user.id}})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

def deleteUser(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = request.POST
		try:
			user = User.objects.get(id=data['id'])
			user.delete()
			return JsonResponse({'result': 'Success', 'message': ''})
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': 'User id not found'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

	

urlpatterns = [
	url(r'^auth', authForm, name='authForm'),
	url(r'^rooms', rooms, name='rooms'),
	url(r'^calendar', calendar, name='calendar'),
	url(r'^createMeeting', createMeeting, name='createMeeting'),
	url(r'^editMeeting', editMeeting, name='editMeeting'),
	url(r'^deleteMeeting', deleteMeeting, name='deleteMeeting'),
	url(r'^requiresLogin', requiresLogin, name='requiresLogin'),

	url(r'^addUser', addUser, name='addUser'),
	url(r'^editUser', editUser, name='editUser'),
	url(r'^deleteUser', deleteUser, name='deleteUser'),
]
