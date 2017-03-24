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

EVENT_COLORS = ["#5aaf44", "#397be5", "#c4210f", "#edc617", "#57b1c1", "#efc4d4", "#095122", "#9be20b"]

def parseMeetingTime(data):
	date = [int(i) for i in data['date'].split('-')]
	time = [int(i) for i in data['time'].split(':')]
	duration = [int(i) for i in data['duration'].split(':')]
	duration = duration[0] * 60 + duration[1]
	start = datetime(date[2], date[1], date[0], time[0], time[1])

	return start, duration

def formatDate(dt):
	return "%02d-%02d-%02d" % (dt.day, dt.month, dt.year)

def formatTime(dt):
	return "%02d:%02d" % (dt.hour, dt.minute)

def getCalendar(request):
	meetings = models.Meeting.objects.all()
	rooms = models.Room.objects.all()
	parsedMeetings = []
	for m in meetings:
		endDate = m.start + timedelta(minutes=m.duration)
		editable = "false"
		if m.user.id == request.user.id or request.user.is_superuser:
			editable = "true"
		parsedMeetings.append({
			'title': m.user.entity.name,
			'start': str(m.start.isoformat()),
			'end': str(endDate),
			'resourceId': m.room.id,
			'editable': editable,
			'data': {
				'id': m.id,
				'entity': m.user.entity.name,
				'description': m.description,
				'date': formatDate(m.start),
				'endDate': formatDate(endDate),
				'time': formatTime(m.start),
				'duration': m.duration,
				'durationTime': "%02d:%02d" % (m.duration // 60, m.duration % 60),
				'room': m.room.id,
			}
		})
		
	roomsSet = {r.id for r in rooms}

	colorMap = {}
	i = 0
	for r in roomsSet:
		if i < len(EVENT_COLORS):
			colorMap[r] = EVENT_COLORS[i]
		else:
			colorMap[r] = EVENT_COLORS[len(EVENT_COLORS)-1]
		i += 1

	parsedRooms = []
	for r in rooms:
		parsedRooms.append({'title': r.name, 'id': r.id, 'eventColor': colorMap[r.id]})
	
	return (parsedMeetings, parsedRooms)

def getUsers(request):
	users = []
	if request.user.is_superuser:
		for u in User.objects.all():
			users.append({'id': u.id, 'name': u.first_name, 'email': u.username, 'entity': u.entity.name})

	return users

