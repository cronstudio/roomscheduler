from main.models import *

EVENT_COLORS = ["#5aaf44", "#397be5", "#c4210f", "#edc617", "#57b1c1", "#efc4d4", "#095122", "#9be20b", "#364b6d", "#e88937", "#c7ef26", "#008faf", "#1f5489", "#ff604f", "#13af88", "#7d2a82", "#6519c1", "#97efcf", "#2fb72f", "#960000", "#17420b", "#257c96", "#594602", "#22f9f9"]
for c in EVENT_COLORS:
	if len(Color.objects.filter(value=c)) == 0:
		Color(value=c).save()

default = Color.objects.get(value="#5aaf44")
for r in Room.objects.all():
	if r.color == None or r.color.id == default.id:
		r.color = Color.objects.filter(room=None).first()
		if r.color == None:
			r.color = Color.objects.get(value="#5aaf44")
		r.save()

print("Colors added!")