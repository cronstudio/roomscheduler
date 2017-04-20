import json

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.models import User, AnonymousUser
from main import models
from django.db.models import Q
from main.models import Room, Meeting, Entity
from datetime import datetime, timedelta
from main.data import *

from django.conf.urls import include, url
from main.helpers import *

def JsonResponse(response_data):
	return HttpResponse(json.dumps(response_data), content_type="application/json")

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
			data = models.Room.objects.filter(active=True).values('id', 'name')
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
		if not models.Room.objects.get(id=int(data['room'])).active:
			return JsonResponse({'result': 'Failed', 'message': 'This room is currently not active'})
		
		meeting = models.Meeting(user=request.user, description=data['description'], start=start, duration=duration, room=models.Room.objects.get(id=int(data['room']) ) )
		meeting = tzAware(meeting)
		result, message = checkMeetingData(None, meeting);
		if not result:
			return JsonResponse({'result': 'Failed', 'message': message})
		else:
			meeting.save()
			return JsonResponse({'result': 'Success', 'data': meeting2FCEvent(meeting, request)})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})


@login_required(redirect_field_name="requiresLogin")
def editMeeting(request):
	if request.method == 'POST':
		data = request.POST
		start, duration = parseMeetingTime(data)
		
		original = models.Meeting.objects.get(id=data['id'])
		meeting = models.Meeting.objects.get(id=data['id'])
		meeting.description = data['description']
		meeting.start = start
		meeting.duration = duration
		meeting.room = models.Room.objects.get(id=int(data['room']) )
		meeting  = tzAware(meeting)
		if not models.Room.objects.get(id=int(data['room'])).active:
			return JsonResponse({'result': 'Failed', 'message': 'This room is currently not active'})
		
		result, message = checkMeetingData(original, meeting)
		if not result:
			return JsonResponse({'result': 'Failed', 'message': message})
		else:
			meeting.save()
			return JsonResponse({'result': 'Success', 'data': meeting2FCEvent(meeting, request)})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def deleteMeeting(request):
	if request.method == 'POST':
		data = request.POST
		
		try:
			meeting = models.Meeting.objects.get(id=data['id'])
			if not request.user.is_superuser and meeting.user.id != request.user.id:
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
	user = None
	if found != None and found.is_active:
		user = auth.authenticate(username=email, password=password)

	response_data = {}
	if user is not None:
		auth.login(request, user)
		response_data['result'] = 'Success'
		response_data['message'] = '';
	else:
		if found != None and found.is_active == False:
			response_data['result'] = 'Failed'
			response_data['message'] = 'A sua conta deve ser activada por um administrador'
		elif found != None:
			response_data['result'] = 'Failed'
			response_data['message'] = 'Password errada!'
		else:
			response_data['result'] = 'Failed'
			response_data['message'] = 'Nenhuma conta encontrada com email'
	
	return JsonResponse(response_data)

'''
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
'''

def logout(request):
	auth.logout(request)
	
	return JsonResponse({'result': 'Success', 'message': 'Logged out successfully'})

def requiresLogin(request):
	return JsonResponse({'result': 'Failed', 'message': 'This action requires login'})

@login_required(redirect_field_name="requiresLogin")
def editUser(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = stripArgs(request.POST)

		try:
			if data['email'] == "" or data['name'] == "" or data['entity'] == "":
				return JsonResponse({'result': 'Failed', 'message': 'Deve preencher todos os campos na edição de um utilizador'})

			password = data['password'].strip()
			user = User.objects.get(id=data['id'])
			userExists = usernameExists(data['email'])
			if userExists != None and userExists.id != user.id:
				return JsonResponse({'result': 'Failed', 'message': 'Este email já pertence a outro utilizador.'})
			
			was_active = user.is_active
			user.username = user.email = data['email']
			user.entity.name = data['entity']
			user.first_name = data['name']
			user.is_active = False if data['active'] == "false" else True
			user.is_superuser = False if data['superuser'] == "false" else True
			if password != "":
				user.set_password(password)
			if was_active and not user.is_active:
				deactivateUser(user)
			elif not was_active and user.is_active:
				activateUser(user)
			user.save()
			return JsonResponse({'result': 'Success', 'message': '', 'refresh': True})
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': 'User id not found'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def addUser(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = stripArgs(request.POST)

		if data['email'] == "" or data['name'] == "" or data['entity'] == "" or data['password'] == "":
			return JsonResponse({'result': 'Failed', 'message': 'Deve preencher todos os campos na criação de um utilizador.'})
		
		print(data)
		user = User()
		userExists = usernameExists(data['email'])
		if userExists != None:
			return JsonResponse({'result': 'Failed', 'message': 'Este email já pertence a outro utilizador'})

		user.email = user.username = data['email']
		user.first_name = data['name']
		user.is_active = False if data['active'] == "false" else True
		user.is_superuser = False if data['superuser'] == "false" else True
		if data['password'] != "":
			user.set_password(data['password'])
		user.save()
		user.entity.name = data['entity']
		user.save()
		return JsonResponse({'result': 'Success', 'message': '', 'data': {'id': user.id}})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def deleteUser(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = stripArgs(request.POST)
		try:
			user = User.objects.get(id=data['id'])
			Meeting.objects.filter(user=data['id']).delete()
			user.delete()
			return JsonResponse({'result': 'Success', 'message': '', 'refresh': True})
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': 'User id not found'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def editRoom(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = stripArgs(request.POST)
		try:
			room = models.Room.objects.get(id=data['id'])
			was_active = room.active
			room.name = data['name']
			room.description = data['description']
			room.active = False if data['active'] == "false" else True
			if was_active and not room.active:
				deactivateRoom(room)
			elif not was_active and room.active:
				activateRoom(room)
			room.save()
			return JsonResponse({'result': 'Success', 'message': '', 'refresh': True})
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': 'Room id not found'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def addRoom(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = stripArgs(request.POST)
		
		room = Room()
		room.name = data['name']
		room.description = data['description']
		room.active = False if data['active'] == "false" else True
		room.color = getNewColor()
		room.save()
		return JsonResponse({'result': 'Success', 'message': '', 'data': {'id': room.id}})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def deleteRoom(request):
	if not request.user.is_superuser:
		return JsonResponse({'result': 'Failed', 'message': 'This action requires admin permissions'})

	if request.method == 'POST':
		data = stripArgs(request.POST)
		try:
			room = Room.objects.get(id=data['id'])
			Meeting.objects.filter(room=data['id']).delete()
			room.delete()
			return JsonResponse({'result': 'Success', 'message': '', 'refresh': True})
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': 'Room id not found'})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})

@login_required(redirect_field_name="requiresLogin")
def activeRooms(request):
	if request.method == 'GET':
		data = request.GET
		try:
			start = parseDatetime(data['start'])
			end = parseDatetime(data['end'])
			rooms = roomsInInterval(start, end)
			_, roomData = getCalendar(request)

			parsedRooms = []
			for r in rooms:
				color = GREY
				if r.active:
					color = r.color.value
				title = r.name
				if not r.active:
					title += ' (Indisponível)'

				parsedRooms.append({'title': title, 'description': r.description, 'id': r.id, 'eventColor': color, 'active': r.active})

			return JsonResponse({'result': 'Success', 'message': '', 'data': {'rooms': parsedRooms} })
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': str(e)})

	return JsonResponse({'result': 'Failed', 'message': 'Invalid http method: expected POST, received ' + request.method})	

@login_required(redirect_field_name="requiresLogin")
def changePassword(request):
	if request.method == 'POST':
		data = request.POST
		user = None
		if 'currentPassword' not in data or 'newPassword' not in data:
			return JsonResponse({'result': 'Failed', 'message': 'Missing arguments'})
		try:
			user = User.objects.get(id=request.user.id, is_active=True)
		except Exception as e:
			return JsonResponse({'result': 'Failed', 'message': 'Login as a valid user required'})
		
		checkPass = user.check_password(data['currentPassword'])
		if not checkPass:
			return JsonResponse({'result': 'Failed', 'message': 'A password actual está errada.'})
		user.set_password(data['newPassword'])
		user.save()
		user = auth.authenticate(username=user.username, password=data['newPassword'])
		auth.login(request, user)
		return JsonResponse({'result': 'Success', 'message': ''})

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

	url(r'^addRoom', addRoom, name='addRoom'),
	url(r'^editRoom', editRoom, name='editRoom'),
	url(r'^deleteRoom', deleteRoom, name='deleteRoom'),

	url(r'^activeRooms', activeRooms, name='activeRooms'),
	url(r'^changePassword', changePassword, name='changePassword'),
]
