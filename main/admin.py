from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Meeting)
admin.site.register(Room)
