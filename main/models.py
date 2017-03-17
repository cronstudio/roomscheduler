from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
	name = models.CharField(max_length=64)
	def __str__(self):
		return self.name

class Meeting(models.Model):
	user = models.ForeignKey(User)
	name = models.CharField(max_length=64)
	start = models.DateTimeField('start')
	duration = models.FloatField()
	room = models.ForeignKey(Room)
	description = models.CharField(max_length=128)

	def __str__(self):
		return self.name + " at " + self.room.name

