from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Meeting(models.Model):
	owner = User()
	start = models.DateTimeField('start')
	duration = models.FloatField()

class Room(models.Model):
	name = models.CharField(max_length=64)

