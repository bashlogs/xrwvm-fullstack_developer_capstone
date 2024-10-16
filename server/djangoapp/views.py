from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import logging
import json
from .models import CarMake, CarModel
from .populate import initiate
from .restapis import get_request, analyze_review_sentiments, post_review

# Get an instance of a logger
logger = logging.getLogger(__name__)

def get_cars(request):
    count = CarMake.objects.filter().count()
    print(count)
    if(count == 0):
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({"CarModel": car_model.name, "CarMake": car_model.car_make.name})
    return JsonResponse({"CarModels":cars})

# Create your views here.

# Create a `login_user` view to handle sign-in requests
@csrf_exempt
def login_user(request):
    if request.method == "POST":
        try:
            # Parse the JSON request data
            data = json.loads(request.body)
            username = data.get('userName')
            password = data.get('password')

            # Authenticate the user
            user = authenticate(username=username, password=password)
            if user is not None:
                # Log the user in
                login(request, user)
                response_data = {"userName": username, "status": "Authenticated"}
            else:
                response_data = {"status": "Error", "message": "Invalid credentials"}
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            response_data = {"status": "Error", "message": "Login failed"}
    else:
        response_data = {"status": "Error", "message": "POST request required"}

    return JsonResponse(response_data)

# Create a `logout_request` view to handle sign-out requests
@csrf_exempt
def logout_request(request):
    if request.method == "POST":
        # Log the user out
        logout(request)
        # Return a JSON response indicating the user has logged out
        response_data = {"userName": "", "status": "Logged out"}
        return JsonResponse(response_data)
    else:
        return JsonResponse({"status": "Error", "message": "POST request required"})

# Create a `registration` view to handle sign-up requests
@csrf_exempt
def registration(request):
    context = {}

    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    email_exist = False
    try:
        # Check if user already exists
        User.objects.get(username=username)
        username_exist = True
    except:
        # If not, simply log this is a new user
        logger.debug("{} is new user".format(username))

    # If it is a new user
    if not username_exist:
        # Create user in auth_user table
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,password=password, email=email)
        # Login the user and redirect to list page
        login(request, user)
        data = {"userName":username,"status":"Authenticated"}
        return JsonResponse(data)
    else :
        data = {"userName":username,"error":"Already Registered"}
        return JsonResponse(data)

# Example placeholder for dealership views
# These views can be customized based on your app's requirements
def get_dealerships(request, state="All"):
    if(state == "All"):
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/"+state
    dealerships = get_request(endpoint)
    return JsonResponse({"status":200,"dealers":dealerships})

def get_dealer_reviews(request,dealer_id):
    if(dealer_id):
        endpoint="/fetchReviews/dealer/"+str(dealer_id)
        reviews=get_request(endpoint)
        for review_detail in reviews:
            response = analyze_review_sentiments(review_detail['review'])
            print(response)
            review_detail['sentiment'] = response['sentiment']
        return JsonResponse({"status":200,"reviews":reviews})
    else:
        return JsonResponse({"status":400,"message":"Bad Request"})

def get_dealer_details(request, dealer_id):
    if(dealer_id):
        endpoint = "/fetchDealer/"+str(dealer_id)
        dealership=get_request(endpoint)
        return JsonResponse({"status":200,"dealer":dealership})

    else:
        return JsonResponse({"status":400,"message":"Bad request"})

def add_review(request):
    
    if(request.user.is_anonymous == False):
        data = json.loads(request.body)
        try:
            response = post_review(data)
            return JsonResponse({"status":200})
        except:
            return JsonResponse({"status":401,"message":"Error in posting review"})
    else:
        return JsonResponse({"status":403,"message":"Unauthorized"})