import json

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.models import User, AnonymousUser

# Create your views here.

def index(request):
	template = loader.get_template('main/index.html')

	content = {}
	user = None
	if request.user.is_authenticated():
		user = request.user
		content['email'] = user.email
		content['loggedIn'] = True
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

def login(request):
	email = request.POST['email']
	password = request.POST['password']
	found = User.objects.get(username=email)
	is_active = found.is_active
	user = auth.authenticate(email=email, username=email, password=password)

	response_data = {}
	if user is not None:
		auth.login(request, user)
		response_data['result'] = 'Success'
		response_data['message'] = ''
	else:
		if found != None and found.is_active == False:
			response_data['result'] = 'Failed'
			response_data['message'] = 'Account not yet active'
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
		user = User.objects.create_user(username=email, password=password)
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
