from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Room(models.Model):
	name = models.CharField(max_length=64)
	def __str__(self):
		return self.name

class Meeting(models.Model):
	user = models.ForeignKey(User) # Also, meeting title on the calendar
	description = models.CharField(max_length=128) # Description of the meeting
	start = models.DateTimeField('start')
	duration = models.FloatField()
	room = models.ForeignKey(Room)

	def __str__(self):
		return "By " + self.user.entity.name + " at " + self.room.name

class Entity(models.Model):
	name = models.CharField(max_length=64)
	user = models.OneToOneField(User, on_delete=models.CASCADE)

	def __str__(self):
		return self.name

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Entity.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.entity.save()

