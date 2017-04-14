from main.models import *
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import connection

def checkMeetingData(orig, m):
	s = m.start
	e = m.start + timedelta(minutes=m.duration)
	now = timezone.now()

	if orig == None or orig.start > now:
		if m.start > now:
			q = """SELECT * FROM main_meeting where room_id=%s and active=1 and not ((start < %s and datetime(start, '+' || duration || ' MINUTES') <= %s) or (start >= %s and datetime(start, '+'|| duration || ' MINUTES') > %s))"""
			meetings = list(Meeting.objects.raw(q, [m.room.id, s, s, e, e]))
			if len(meetings) == 0 or (len(meetings) == 1 and m.id != None and meetings[0].id == m.id):
				return (True, '')
			else:
				reason = "Este espaço encontra-se ocupado à hora pretendida"
		else:
			reason = 'Não é possível marcar reuniões para o passado'
	else:
		reason = 'Não é possível editar reuniões que já começaram'

	return (False, reason)

def roomsInInterval(s, e):
	cursor = connection.cursor()
	c = cursor.execute("SELECT DISTINCT r.id, r.name, r.description, r.active, r.color_id from main_room as r, main_meeting as m where (m.active and not ((start < %s and datetime(start, '+' || duration || ' MINUTES') <= %s) or (start >= %s and datetime(start, '+'|| duration || ' MINUTES') > %s)) and m.room_id=r.id) or r.active", [s,s,e,e])
	rooms = []
	for r in c.fetchall():
		rooms.append(Room(id=r[0], name=r[1], description=r[2], active=r[3], color=Color.objects.get(id=r[4])))
	return rooms

def filterNeededRooms():
	return list(Room.objects.raw("SELECT DISTINCT r.* FROM main_room as r, main_meeting as m WHERE m.room_id=r.id or r.active"))

def usernameExists(email):
	users = list(User.objects.filter(username=email))
	if len(users) == 0:
		return None
	else:
		return users[0]
