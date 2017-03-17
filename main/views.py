import json

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User, AnonymousUser
from main import models
from datetime import datetime, timedelta

# Create your views here.

EVENT_COLORS = ["#5aaf44", "#397be5", "#c4210f", "#edc617", "#57b1c1", "#efc4d4", "#095122", "#9be20b"]

def calendardemo(request):
	template = loader.get_template('main/calendardemo.html')
	return HttpResponse(template.render({}, request))

def formatDate(dt):
	return "%02d-%02d-%02d" % (dt.day, dt.month, dt.year)

def formatTime(dt):
	return "%02d:%02d" % (dt.hour, dt.minute)

def index(request):
	template = loader.get_template('main/index.html')

	content = {}
	user = None
	if request.user.is_authenticated():
		user = request.user
		content['email'] = user.email
		content['loggedIn'] = True
		meetings = models.Meeting.objects.all()
		rooms = models.Room.objects.all()
		#2014-06-09T16:00:00
		parsedMeetings = []
		for m in meetings:
			endDate = m.start + timedelta(minutes=m.duration)
			parsedMeetings.append({
				'title': m.name,
				'start': str(m.start.isoformat()),
				'end': str(endDate),
				'room': m.room.id,
				'data': {
					'name': m.name,
					'description': m.description,
					'date': formatDate(m.start),
					'endDate': formatDate(endDate),
					'time': formatTime(m.start),
					'duration': m.duration,
					'durationTime': "%02d:%02d" % (m.duration // 60, m.duration % 60),
					'room': m.room.id,
				}
			})
			print(m.duration)
			
		roomsSet = {r.id for r in rooms}

		colorMap = {}
		i = 0
		for r in roomsSet:
			print("color", i)
			if i < len(EVENT_COLORS):
				colorMap[r] = EVENT_COLORS[i]
			else:
				colorMap[r] = EVENT_COLORS[len(EVENT_COLORS)-1]
			i += 1


		parsedRooms = []
		for r in rooms:
			parsedRooms.append({'name': r.name, 'id': r.id, 'color': colorMap[r.id]})

		print(parsedMeetings, parsedRooms)
		content['meetings'] = parsedMeetings
		content['rooms'] = parsedRooms
	else:
		content['loggedIn'] = False
	return HttpResponse(template.render(content, request))

def authForm(request):
	if request.method == 'POST':
		print(request.POST['action'])
		if request.POST['action'] == 'login':
			return login(request)
		elif request.POST['action'] == 'register':
			return register(request)
		elif request.POST['action'] == 'logout':
			return logout(request)

def rooms(request):
	if request.method == 'GET':
		data = models.Room.objects.all().values('id', 'name')
		return JsonResponse({'rooms': list(data)})

def saveMeeting(request):
	if request.method == 'POST':
		data = request.POST
		print(data)
		print(data.keys())
		date = [int(i) for i in data['date'].split('-')]
		time = [int(i) for i in data['time'].split(':')]
		duration = [int(i) for i in data['duration'].split(':')]
		duration = duration[0] * 60 + duration[1]
		start = datetime(date[2], date[1], date[0], time[0], time[1])
		print(data['title'], data['description'])
		meeting = models.Meeting(user=request.user, name=data['title'], description=data['description'], start=start, duration=duration, room=models.Room.objects.get(id=int(data['room']) ) )
		meeting.save()
		return JsonResponse({'result': 'Success'})

	return JsonResponse({'result': 'Failed'})

def login(request):
	email = request.POST['email']
	password = request.POST['password']
	found = None
	l = User.objects.filter(username=email)
	if len(l) > 0:
		found = User.objects.get(username=email)
	user = auth.authenticate(email=email, username=email, password=password)

	response_data = {}
	if user is not None:
		auth.login(request, user)
		response_data['result'] = 'Success'
		response_data['message'] = ''
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
	request.session.flush()
	request.user = AnonymousUser

	return JsonResponse({'result': 'Success', 'message': 'logged out successfully'})
