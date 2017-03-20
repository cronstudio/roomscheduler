from main.models import *
from datetime import *

def checkMeetingData(m):
	s = m.start
	e = m.start + timedelta(minutes=m.duration)
	q = """SELECT * FROM main_meeting where room_id=%s and not ((start < %s and datetime(start, '+' || duration || ' MINUTES') <= %s) or (start >= %s and datetime(start, '+'|| duration || ' MINUTES') > %s))"""
	print([m.room.id, s, s, e, e])
	meetings = list(Meeting.objects.raw(q, [m.room.id, s, s, e, e]))
	for i in meetings:
		print(i.name, i.start, i.start + timedelta(minutes=i.duration))
	print("Meetings:", len(meetings))
	if len(meetings) == 0 or (len(meetings) == 1 and m.id != None and meetings[0].id == m.id):
		return (True, '')
	else:
		return (False, "Este espaço encontra-se ocupado à hora pretendida")

