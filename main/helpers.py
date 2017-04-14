import json
from django.utils import timezone

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User, AnonymousUser
from main import models
from datetime import datetime, timedelta
from main.data import checkMeetingData, roomsInInterval, filterNeededRooms
from django.utils.dateparse import parse_datetime

#EVENT_COLORS = ["#5aaf44", "#397be5", "#c4210f", "#edc617", "#57b1c1", "#efc4d4", "#095122", "#9be20b"]
GREY = "#aaaaaa"
LOCALTZ = timezone.get_current_timezone()

def parseMeetingTime(data):
	date = [int(i) for i in data['date'].split('-')]
	time = [int(i) for i in data['time'].split(':')]
	duration = [int(i) for i in data['duration'].split(':')]
	duration = duration[0] * 60 + duration[1]
	start = datetime(date[2], date[1], date[0], time[0], time[1], tzinfo=LOCALTZ)
	return start, duration

def formatDate(dt):
	return "%02d-%02d-%02d" % (dt.day, dt.month, dt.year)

def formatTime(dt):
	return "%02d:%02d" % (dt.hour, dt.minute)

def tzAware(m):
	if m.start.tzinfo is None or m.start.tzinfo.utcoffset(m.start) is None:
		m.start = timezone.localtime(m.start)
	
	return m

def checkMeetingDates(m):
	return (True, '')

def meeting2FCEvent(m, request): # output date: database utc to local timezone
	now = timezone.now()
	m = tzAware(m)
	endDate = m.start + timedelta(minutes=m.duration)
	startEditable = False
	durationEditable = False
	editable = False
	if m.user.id == request.user.id or request.user.is_superuser:
		if m.start > now:
			startEditable = True
			editable = True
			durationEditable = True

	
	m.start = m.start
	endDate = endDate
	return {
		'title': m.user.entity.name,
		'start': str(m.start.isoformat()),
		'end': str(endDate),
		'resourceId': m.room.id,
		'editable': 'true' if editable else 'false',
		'startEditable': 'true' if startEditable else 'false',
		'durationEditable': 'true' if durationEditable else 'false',
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
			'roomName': m.room.name,
		}
	}


def getCalendar(request):
	now = timezone.now()

	meetings = models.Meeting.objects.filter(active=True)
	rooms = None
	if request.user.is_superuser:
		rooms = models.Room.objects.all()
	else:
		rooms = filterNeededRooms()

	parsedMeetings = []
	for m in meetings:
		if not m.active:
			continue
		
		parsedMeetings.append(meeting2FCEvent(m, request))
		
	parsedRooms = []
	for r in rooms:
		color = GREY
		if r.active:
			color = r.color.value
		parsedRooms.append({'title': r.name, 'description': r.description, 'id': r.id, 'eventColor': color, 'active': r.active})
	
	return (parsedMeetings, parsedRooms)

def getUsers(request):
	users = []
	if request.user.is_superuser:
		for u in User.objects.all():
			users.append({'id': u.id, 'name': u.first_name, 'email': u.username, 'entity': u.entity.name, 'active': u.is_active, 'superuser': u.is_superuser})

	return users

def deactivateUser(user):
	now = timezone.now()
	models.Meeting.objects.filter(user=user.id, start__gte=now).update(active=False)

def activateUser(user):
	now = timezone.now()
	models.Meeting.objects.filter(user=user.id, start__gte=now).update(active=True)

def deactivateRoom(room):
	now = timezone.now()
	models.Meeting.objects.filter(room=room.id, start__gte=now).update(active=False)

def activateRoom(room):
	now = timezone.now()
	models.Meeting.objects.filter(room=room.id, start__gte=now).update(active=True)

def parseDatetime(dt):
	d, t = dt.split(' ')
	s = d.split('-') + t.split(':')
	return datetime(*[int(i) for i in s])

def getNewColor():
	color = models.Color.objects.filter(room=None).first()
	if color == None:
		color = models.Color.objects.get(value="#5aaf44")
	return color


def stripArgs(args):
	data = {}
	for k in args:
		data[k] = args[k].strip()
	return data
