from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import django.core.exceptions
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.csrf import csrf_exempt

from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django.utils import timezone
from django.db.models import Q, Sum
# from django.core.urlresolvers import reverse
from django.urls import reverse_lazy, reverse

# Python imports 
#from datetime import timedelta
import datetime
import uuid
import random
import os

# Bullets imports
from .forms import RegisterForm, UnRegisterForm, ContactForm, NewsForm, RunningEventForm, BulletEventForm, IWDForm, BigBulletRiderForm
from .models import Bullet, OldBullet, News, RunningEvent, ActivityCache, BulletEvent, IWDRider, BigBulletRider, FredRider, FredHighLeaderBoard, FredLowLeaderBoard 

from .utils import send_bullet_mail, who_to_email, send_manager_email 

# SALEOR imports
from saleor.core.utils import build_absolute_uri


import mailchimp  # for adding users to our mailing list
import logging    # For the logging library

from stravalib import Client, unithelper

# Get an instance of a logger
logger = logging.getLogger(__name__)



# Decorator style for checking login status
def is_core_team(user):
    return user.groups.filter(name='CoreTeam').exists()

# Decorator style for checking login status
def is_stats_team(user):
    return user.groups.filter(name='StatsTeam').exists()



def index(request):
    # Get the cached number of Strava Runners and Cylists
    strava_runners = request.site.settings.runners 
    strava_cyclists = request.site.settings.cyclists

    now = timezone.now()

    week_run_miles =  ActivityCache.objects.filter(activity_type=ActivityCache.RUN).filter(start_date__gte=(now-datetime.timedelta(days=7))).aggregate(Sum('distance'))['distance__sum']
    week_ride_miles =  ActivityCache.objects.filter(activity_type=ActivityCache.RIDE).filter(start_date__gte=(now-datetime.timedelta(days=7))).aggregate(Sum('distance'))['distance__sum']

    year_run_miles = ActivityCache.objects.filter(activity_type=ActivityCache.RUN).filter(start_date__year=now.year).aggregate(Sum('distance'))['distance__sum']

    year_ride_miles = ActivityCache.objects.filter(activity_type=ActivityCache.RIDE).filter(start_date__year=now.year).aggregate(Sum('distance'))['distance__sum']

    week_runs = ActivityCache.objects.filter(activity_type=ActivityCache.RUN).filter(start_date__gte=(now-datetime.timedelta(days=7))).count()
    week_rides = ActivityCache.objects.filter(activity_type=ActivityCache.RIDE).filter(start_date__gte=(now-datetime.timedelta(days=7))).count()

    year_runs = ActivityCache.objects.filter(activity_type=ActivityCache.RIDE).filter(start_date__year=now.year).count()
    year_rides = ActivityCache.objects.filter(activity_type=ActivityCache.RUN).filter(start_date__year=now.year).count()
 
    qs = News.objects.order_by("-date_added")
    qs = qs.filter(Q(display_after__lte=now) | Q(display_after=None))
    qs = qs.filter(Q(display_until__gte=now) | Q(display_until=None))
    qs = qs.filter(front_page=True)  

    cycling_first = True
    if (random.random() > 0.5):
        cycling_first = False


    return render(request, "bullets/index.html", {'strava_runners':strava_runners, 'strava_cyclists':strava_cyclists, 'week_run_miles':week_run_miles, 'week_ride_miles':week_ride_miles,'year_run_miles':year_run_miles, 'year_ride_miles':year_ride_miles, 'week_runs':week_runs, 'week_rides':week_rides, 'year_runs':year_runs, 'year_rides':year_rides, 'news':qs, 'year':now.year, 'cycling_first':cycling_first})


	

# Add a user to our mailing list
def add_to_mailchimp(email):
    try:
        m = mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)
        m.lists.subscribe(settings.MAILCHIMP_LISTID, {'email': email}, double_optin=False, send_welcome=True)
        return True
    except mailchimp.ListAlreadySubscribedError:
        return True
    except mailchimp.Error as e:
        s = 'add_to_mailchimp for (%s) - error : %s - %s' % (email, e.__class__, e)
        logger.error(s)
        return False

# Remove a user from our mailing list (on unregistration as a bullet)
def remove_from_mailchimp(email):
    try:
        m = mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)
        m.lists.unsubscribe(settings.MAILCHIMP_LISTID, {'email': email})
    except mailchimp.Error as e:
        s = 'add_to_mailchimp for (%s) - error : %s - %s' % (email, e.__class__, e)
        logger.error(s)
        return False


# Register a new bullet onto the system
def register(request): 
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        register_form = RegisterForm(request.POST)
        # check whether it's valid:
        if register_form.is_valid():
            # check to see if someone with same name & email address has already registered
            x = Bullet.objects.filter(email__iexact=register_form.cleaned_data["email"], name__iexact=register_form.cleaned_data["name"]).exists()
            if x:
                messages.info(request, "You are already registered as a Boldmere Bullet!")
                return redirect(reverse('already-registered'))


            bullet = register_form.save()
            url = reverse('confirm-bullet-email', args=[bullet.email_check_ref])
            url = build_absolute_uri(url)

            context = register_form.cleaned_data
            context['confirm_url'] = url

            bullet.send_email(
                template="bullets/register", 
                context=context, 
                override_email_safety=True)  # Override the safety check as we want them to confirm their email address
 
            messages.success(request, 'You have successfully registered with the Boldmere Bullets!');
            return redirect(reverse('registered'))
   
        # if a GET (or any other method) we'll create a blank form
    else:
        register_form = RegisterForm()

    return render(request, "bullets/registration/register.html", {'register_form':register_form})


# Handle confirmation of a new email address for a bullet
def confirm_email(request, uuid):
    bullet = get_object_or_404(Bullet, email_check_ref=uuid)
    if (bullet.email_checked == None):
        bullet.confirm_email()
        if bullet.get_emails:
            x = add_to_mailchimp(bullet.email)
            if x:
                messages.success(request, "Thank you " + str(bullet.name) + "! You have been added to the Boldmere Bullets email list.")
            else:
                messages.info(request, "There was a problem adding your email to the Boldmere Bullets email list - we'll look into it.")

        else:
            messages.success(request, "Thank you for confirming your email address " + str(bullet.name))

    else:
        messages.info(request, "That page has expired")
        
    return redirect(reverse('index'))


# when a bullet asks to unregister we send them an email to check it is really them
def confirm_remove(request, uuid):
    bullet = get_object_or_404(Bullet, email_check_ref=uuid)
    messages.success(request, "Thank you for unregistering from the Boldmere Bullets " + str(bullet.name))

    if bullet.get_emails:
        remove_from_mailchimp(bullet.email)

    bullet.delete()

    return redirect(reverse('unregistered'))


# A bullet wishes to unregister from us
def unregister(request): 
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        unregister_form = UnRegisterForm(request.POST)
        # check whether it's valid:
        if unregister_form.is_valid():
            try:	
                email = unregister_form.cleaned_data["email"]
                bullets = Bullet.objects.filter(email__iexact=email)
                
                for bullet in bullets:					
                    # Because there can be multiple bullets on a single email - email them all
                    bullet.email_check_ref = uuid.uuid4()   # update the unique ref 
                    bullet.save()

                    unregister_url = reverse('unregister-bullet-email', args=[bullet.email_check_ref])
                    unregister_url = build_absolute_uri(unregister_url)
                    context = {'name': bullet.name, 'unregister_url':unregister_url}

                    bullet.send_email(
                        template="bullets/unregister", 
                        context=context, 
                        override_email_safety=True)

                messages.success(request, 'Please check your email to confirm unregistration')
            except:
                messages.warning(request, 'There was a problem removing your registration - sorry!')	
									
        return redirect(reverse('index'))
    # if a GET (or any other method) we'll create a blank form
    else:
        unregister_form = UnRegisterForm()
   
    return render(request, "bullets/registration/unregister.html", {'unregister_form':unregister_form})
       


# Mailchimp Callback URL
@csrf_exempt
def mailchimp_webhook(request, apikey):
    # called when a user manually unsubscribes from the mailing list - so we should mark them as no longer wanting emails and ask if 
    # they no longer wish to be bullets

    # step 1 - is this a valid request from mailchimp - does the secret apikey match?
    if apikey != settings.MAILCHIMP_WEBHOOK_APIKEY:
        logger.error("Received a mailchimp webhook but API KEY did not match (%s)" % apikey)
        return redirect(reverse('index'))

    # step 2 - check this is an unsubscribe event
    action = request.POST.get("data[action]", None)
    if (action != 'unsub') and (action != 'delete'):
        logger.error("Action from mailchimp webhook is not supported (%s)" % action)
        return redirect(reverse('index'))

    # step 3 - get the email address from the web hook
    email = request.POST.get("data[email]", None)
    if email == None:
        logger.error("No email from mailchimp webhook API")
        return redirect(reverse('index'))

    # step 4 - get all of the bullets associated with this email address
    bullets = Bullet.objects.filter(email__iexact=email)
                
    for bullet in bullets:					
        # Because there can be multiple bullets on a single email - email them all
        bullet.email_check_ref = uuid.uuid4()   # update the unique ref 
        bullet.get_emails = False		# They definitely want out of emails
        bullet.save()

        unregister_url = reverse('unregister-bullet-email', args=[bullet.email_check_ref])
        unregister_url = build_absolute_uri(unregister_url)
        context = {'name': bullet.name, 'unregister_url':unregister_url}

        bullet.send_email(
            template="bullets/unregister_list", 
            context=context, 
            override_email_safety=True)
   
    return redirect(reverse('index'))





# Handle contact form 
def contact(request): 
	if request.method == 'POST':
        	# create a form instance and populate it with data from the request:
		contact_form = ContactForm(request.POST)
        	# check whether it's valid:
		if contact_form.is_valid():
			context = contact_form.cleaned_data 

			send_manager_email(
        			template_name='bullets/contact',
                                extra_headers={'Reply-To':contact_form.cleaned_data['email']},
        			context=context)

			send_bullet_mail(
        			template_name='bullets/contact_thanks',
               			recipient_list=[contact_form.cleaned_data['email']],
        			context={})

			messages.success(request, 'Your message has been sent to the Boldmere Bullets!');
			            
			return redirect(reverse('index'))

   		 # if a GET (or any other method) we'll create a blank form
	else:
		contact_form = ContactForm()
   
	return render(request, "bullets/contact-us.html", {'contact_form':contact_form})



#### TUESDAY RUN VIEW 
def run_tuesday(request):		# get the list of runs
	now = timezone.now()
	q = RunningEvent.objects.filter(date__gte=now)
	return render(request, "bullets/run_tuesday.html", {'runs':q})


### Events view
def events(request):
    now = timezone.now()
    q = BulletEvent.objects.filter(date__gte=now).order_by('date')
    return render(request, "bullets/events.html", {'events':q})



### NEWS VIEWS
class NewsListView(ListView):
	model = News
	template_name = 'core/news_list.html' 
	context_object_name = 'stories'  
	paginate_by = 3

	def get_queryset(self):
		now = timezone.now()

		qs = News.objects.order_by("-date_added")
		qs = qs.filter(Q(display_after__lte=now) | Q(display_after=None))
		qs = qs.filter(Q(display_until__gte=now) | Q(display_until=None))
		return qs
  

def news_item(request, slug):
	story = get_object_or_404(News, slug=slug)
	if story.redirect_to:
		return redirect(story.redirect_to)

	return render(request, "bullets/news_item.html", {'story':story})



# View to handle IWD rider registrations
def iwd_register(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        iwd_form = IWDForm(request.POST)
        	# check whether it's valid:
        if iwd_form.is_valid():
            iwd = iwd_form.save()
            
            unregister_evans_url = build_absolute_uri(reverse('iwd-unregister', args=['evans', iwd.email_check_ref]))
            unregister_ride_url = build_absolute_uri(reverse('iwd-unregister', args=['ride', iwd.email_check_ref]))
            ride_info_url = build_absolute_uri(reverse('ride-info'))

            context = {'iwd':iwd, 'unregister_evans_url':unregister_evans_url, 'unregister_ride_url':unregister_ride_url, 'ride_info_url':ride_info_url} 

            send_bullet_mail(
                template_name='bullets/iwd',
                recipient_list=[iwd.email],
                context=context)
			
            messages.success(request, "You have successfully registered - we will email you to confirm!");
			            
            return redirect(reverse('index'))

   	# if a GET (or any other method) we'll create a blank form
    else:
        iwd_form = IWDForm()
   
    return render(request, "bullets/iwd/register.html", {'form': iwd_form})

# someone no longer wants to do the IWD ride
def iwd_unregister(request, event_type, uuid):
    iwd = get_object_or_404(IWDRider, email_check_ref=uuid)
    if request.method == 'POST':
        if event_type == 'evans':
            iwd.evans = False
            messages.success(request, "Thank you for unregistering from the Evans Bike Maintenance event, " + str(iwd.name))
        elif event_type == 'ride':
            iwd.speed = IWDRider.NO
            messages.success(request, "Thank you for unregistering from the Womens Interclub Ride, " + str(iwd.name))
        elif event_type == 'both':
            iwd.evans = False
            iwd.speed = IWDRider.NO
            messages.success(request, "Thank you for unregistering from these events, " + str(iwd.name))

        iwd.save()

        if ((iwd.evans == False) and (iwd.doing_ride() == False)):
            iwd.delete()

        return redirect(reverse('index'))
    else:
        return render(request, "bullets/iwd/unregister.html", {'iwd':iwd})






#### CORE TEAM VIEWS ####


### Main page for the core team
@login_required
@user_passes_test(is_stats_team, login_url="/") # are they in the stats team group?    
def bullets_core_team(request):
    messages.info(request, 'Only members of the core team can view this page!')

    bullets = Bullet.objects.count()

    last_week = timezone.now() - datetime.timedelta(days=7)
    last_month = timezone.now() - datetime.timedelta(days=30)

    bullets_week = Bullet.objects.filter(date_added__gte=last_week).count()
    bullets_month = Bullet.objects.filter(date_added__gte=last_month).count()

    news_items = News.objects.order_by("-date_added")

    big_bullets_riders = BigBulletRider.objects.all().count()

    can_edit = is_core_team(request.user)

    return render(request, "bullets/admin/core_team.html", {'bullets':bullets, 'bullets_week':bullets_week, 'bullets_month':bullets_month, 'news_items':news_items, 'big_bullets_riders':big_bullets_riders, 'can_edit':can_edit})



# IWD view
class IWDList(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = IWDRider
    template_name = "bullets/iwd/iwd_list_admin.html"
    def test_func(self):
        return is_core_team(self.request.user)

class IWDUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = IWDRider
    form_class = IWDForm
    success_url = reverse_lazy('iwd-list-admin')
    def test_func(self):
        return is_core_team(self.request.user)

class IWDDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = IWDRider
    success_url = reverse_lazy('iwd-list-admin')  
    def test_func(self):
        return is_core_team(self.request.user)



#### News editing code
class NewsListAdmin(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = News
    template_name = "bullets/news_list_admin.html"
    def test_func(self):
        return is_core_team(self.request.user)
        

class NewsCreate(LoginRequiredMixin, UserPassesTestMixin,CreateView):
    model = News
    form_class = NewsForm
    success_url = reverse_lazy('news-list-admin')
    def test_func(self):
        return is_core_team(self.request.user)

 
class NewsUpdate(LoginRequiredMixin, UserPassesTestMixin,UpdateView):
    model = News
    form_class = NewsForm
    success_url = reverse_lazy('news-list-admin')
    def test_func(self):
        return is_core_team(self.request.user)

class NewsDelete(LoginRequiredMixin, UserPassesTestMixin,DeleteView):
    model = News
    success_url = reverse_lazy('news-list-admin')  
    def test_func(self):
        return is_core_team(self.request.user)


### Event editing code
class EventListAdmin(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = BulletEvent
    template_name = "bullets/event_list_admin.html"
    def test_func(self):
        return is_core_team(self.request.user)
        

class EventCreate(LoginRequiredMixin, UserPassesTestMixin,CreateView):
    model = BulletEvent
    form_class = BulletEventForm
    success_url = reverse_lazy('event-list-admin')
    def test_func(self):
        return is_core_team(self.request.user)

 
class EventUpdate(LoginRequiredMixin, UserPassesTestMixin,UpdateView):
    model = BulletEvent
    form_class = BulletEventForm
    success_url = reverse_lazy('event-list-admin')
    def test_func(self):
        return is_core_team(self.request.user)

class EventDelete(LoginRequiredMixin, UserPassesTestMixin,DeleteView):
    model = BulletEvent
    success_url = reverse_lazy('event-list-admin')  
    def test_func(self):
        return is_core_team(self.request.user)



## Edit Tuesday Runs

@login_required
@user_passes_test(is_core_team, login_url="/") # are they in the core team group?
def run_tuesday_admin(request):
	now = timezone.now()
	q = RunningEvent.objects.filter(date__gte=now)

	if request.method == 'POST':
		run_form = RunningEventForm(request.POST)
		if run_form.is_valid():
			run = run_form.save()
			messages.success(request, "Added run to the system!")
			run_form = RunningEventForm()
			
	else:
		run_form = RunningEventForm()
	
	return render(request, "bullets/run_tuesday_admin.html", {'runs':q, 'run_form':run_form})

	
@login_required
@user_passes_test(is_core_team, login_url="/") # are they in the core team group?
def run_tuesday_admin_delete(request, pk):
	run = get_object_or_404(RunningEvent, pk=pk)
	if request.POST:
		run.delete()
		messages.success(request, "Runn was deleted!")
		return redirect(reverse('run-tuesday-admin'))

	return render(request, "bullets/run_tuesday_delete.html", {'run':run})


# Big Bullets Ride / 10-10 thing admin
class BBRList(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = BigBulletRider
    template_name = "bullets/big_bullets_ride_list_admin.html"
    def test_func(self):
        return is_core_team(self.request.user)



### big bullets ride registration ###

def big_bullets_ride(request):
    if request.POST:
        rider_form = BigBulletRiderForm(request.POST)

        if rider_form.is_valid():
            rider = rider_form.save()

            total_url = build_absolute_uri(reverse('big-bullets-ride-total'))
            cancel_url = build_absolute_uri(reverse('big-bullets-ride-delete', args=[rider.email_check_ref])) 
            rider.send_email(
                template="bullets/big_bullets_register", 
                context={'total_url':total_url, 'rider':rider, 'cancel_url': cancel_url}, 
                override_email_safety=True)

            messages.success(request, "You have been registered!")

            client = Client()
            url = build_absolute_uri(reverse('big-bullets-confirm-strava', args=[rider.email_check_ref])) 
            strava_url = client.authorization_url(client_id=settings.STRAVA_CLIENT_ID, redirect_uri=url) 
            #print("URL = " + str(url))

            return render(request, "bullets/big_bullets_ride_strava.html", {'strava_url':strava_url, 'rider':rider})

    else:
        rider_form = BigBulletRiderForm()
    
    return render(request, "bullets/big_bullets_ride.html", {'rider_form':rider_form})



def big_bullets_ride_confirm_strava(request, uuid):
    rider = get_object_or_404(BigBulletRider, email_check_ref=uuid)

    code = request.GET.get("code", None)

    if code != None:
        client = Client()
        access_token = client.exchange_code_for_token(client_id=settings.STRAVA_CLIENT_ID, client_secret=settings.STRAVA_CLIENT_SECRET, code=code)
        rider.access_token = access_token
        rider.save()
        
        messages.success(request, "We have successfully authorised your Strava account")
    else:
        messages.error(request, "There was a problem authorising us onto your Strava account")
    
    return render(request, "bullets/big_bullets_ride_thanks.html", {'rider':rider})    

def big_bullets_ride_total(request):
    total_distance = 5320
    # TODO: make it actually work
    return render(request, "bullets/big_bullets_ride_total.html", {'total_distance': total_distance})  
 
# someone no longer wants to do the big bullets ride
def big_bullets_ride_delete(request, uuid):
    rider = get_object_or_404(BigBulletRider, email_check_ref=uuid)
    if request.method == 'POST':
        messages.success(request, "Thank you for unregistering from this event, " + str(rider.name))
        rider.delete()

        return redirect(reverse('index'))
    else:
        return render(request, "bullets/big_bullets_ride_delete.html", {'rider':rider}) 


# FRED WHITTINGTON CHALLENGE #

def fred_reg(request):
    rider_id = request.session.get('fred_athlete_id', None)
    if (rider_id != None) and (FredRider.objects.filter(pk=rider_id).exists() != True):
        del request.session['fred_athlete_id']
        del request.session['fred_task_id']


    client = Client()
    url = build_absolute_uri(reverse('fred-confirm-strava')) 
    strava_url = client.authorization_url(client_id=settings.STRAVA_CLIENT_ID, redirect_uri=url) 
      
    return render(request, "bullets/fred/start.html", {'strava_url':strava_url, 'rider_id':rider_id})


def fred_confirm_strava(request):
    code = request.GET.get("code", None)

    if code != None:
        client = Client()
        access_token = client.exchange_code_for_token(client_id=settings.STRAVA_CLIENT_ID, client_secret=settings.STRAVA_CLIENT_SECRET, code=code)
        client.access_token = access_token
        athlete = client.get_athlete()
        rider = FredRider()
        rider.access_token = access_token
        rider.name = str(athlete.firstname) + " " + str(athlete.lastname)
        rider.email = str(athlete.email)
        rider.save()

        result = fred_update_leaderboard.delay(rider_id=rider.id)

        messages.success(request, "We have successfully authorised your Strava account")

        request.session['fred_task_id'] = result.task_id 
        request.session['fred_athlete_id'] = rider.id

        return redirect(reverse('fred-refreshing-progress'))

    
    messages.error(request, "There was a problem authorising us onto your Strava account")
    return redirect(reverse('index'))


# This is the Ajax-y page to show progress on the import
def fred_refreshing_progress(request):
    rider_id = request.session.get('fred_athlete_id', None)
    task_id = request.session.get('fred_task_id', None)

    if (rider_id == None) or (task_id == None):
        return redirect(reverse('fred'))
        
    ajax_url = reverse('fred-get-ajax-progress', args=[task_id])

    return render(request, "bullets/fred/refresh.html", {'ajax_url':ajax_url})



# This view refreshes the athlete's leaderboards via a grab from Strava
def fred_refresh(request):
    rider_id = request.session.get('fred_athlete_id', None)
    print(str(rider_id))
    if rider_id == None:
        return redirect(reverse('fred'))

    rider = get_object_or_404(FredRider, pk=rider_id)
    result = fred_update_leaderboard.delay(rider.id)

    response = redirect(reverse('fred-refreshing-progress'))

    request.session['fred_task_id'] = result.task_id

    return response


# This view shows us how the athlete is getting on in the challenge - their leaderboards and the overall ones
# TODO: overnight update of the leaderboards?
def fred_progress(request):
    rider_id = request.session.get('fred_athlete_id', None)

    if rider_id == None:
        return redirect(reverse('fred'))

    rider = get_object_or_404(FredRider, pk=rider_id)
    
    my_low_board = FredLowLeaderBoard.objects.filter(rider=rider)[:10]
    my_high_board = FredHighLeaderBoard.objects.filter(rider=rider)[:10]

    overall_low_board = FredLowLeaderBoard.objects.all()[:10]
    overall_high_board = FredHighLeaderBoard.objects.all()[:10]

    return render(request, "bullets/fred/progress.html", {'my_low_board':my_low_board, 'my_high_board': my_high_board, 'overall_low_board':overall_low_board, 'overall_high_board':overall_high_board, 'rider':rider})



from celery import shared_task, task
from celery.result import AsyncResult
import celery
from django.http import JsonResponse

# This is the view that returns which rides we've processed so far so we can have a nice ajax-y page to show import progress
def fred_get_ajax_progress(request, task_id):
    job = AsyncResult(task_id)
    results = {'state': str(job.state)}
    if job.state == "PROGRESS":
        results['activity'] = job.result['activity']
    elif job.state == "SUCCESS":
        messages.success(request, "We added " + str(job.result) + " rides to your leaderboards")
    
    return JsonResponse(results)

# update the leaderboard for this rider - go and get their most recent activities
@task(bind=True)
def fred_update_leaderboard(self, rider_id):
    rider = get_object_or_404(FredRider, pk=rider_id)

    client = Client()
    client.access_token = rider.access_token
    if rider.checked_upto_date:
        after_date = rider.checked_upto_date - datetime.timedelta(days=30)
    else:
        after_date = datetime.datetime(2018, 7, 1)
    to_date = datetime.datetime.now()

    added = 0
    for segment in [18298511, 1277267, 6862687, 7224903]:
        added = added + fred_update_segments(self, client, after_date, to_date, segment, rider)
    
    rider.checked_upto_date = to_date
    rider.save()

    return added


# This is a helper function to get the rider's activities on a given segment and (if needed) add to the leaderboard
def fred_update_segments(s, client, after_date, to_date, segment_id, rider):
    segment_efforts = client.get_segment_efforts(segment_id=segment_id, start_date_local=after_date, end_date_local=to_date)
    added = 0

    for seg_eff in segment_efforts:
        activity = seg_eff.activity
        act_detail = client.get_activity(activity.id)
        s.update_state(state='PROGRESS', meta={'activity': act_detail.name})

        distance = unithelper.miles(act_detail.distance).num 
        elevation = unithelper.feet(act_detail.total_elevation_gain)

        if (distance > 40.0): # this is an entry for the long & flat leaderboard
            obj, created = FredLowLeaderBoard.objects.get_or_create(rider=rider, strava_activity_id=activity.id, defaults={'distance':distance, 'elevation':elevation, 'start_date':act_detail.start_date})
            if created:
                added = added + 1

        if (distance <= 40.0):
            obj, created = FredHighLeaderBoard.objects.get_or_create(rider=rider, strava_activity_id=activity.id, defaults={'distance':distance, 'elevation':elevation, 'start_date':act_detail.start_date})
            if created:
                added = added + 1

    return added


##### Chase the Sun calculator ###########
from bullets.forms import CTSTime
def cts(request):
	now = timezone.now()

	if request.POST:
		cts_timeform = CTSTime(request.POST)
		# work out results
		if cts_timeform.is_valid():
			stop = cts_timeform.cleaned_data['stop']
			stop_time =cts_timeform.cleaned_data['time_left']

			stop_names = dict(cts_timeform.STOPS)
			stop_name = stop_names[stop]

			stop_results_dict = {
					32 : "Cheer Point 2", 
					42 : "Support Stop 1",
					71 : "Support Stop 2",
					81 : "Cheer Point 3",
					100 : "Support Stop 3",
					115 : "Cheer Point 4",
					136 : "Support Stop 4",
					150 : "Cheer Point 5",
					166 : "Support Stop 5",
					186 : "Support Stop 6",
					209 : "End",
					}
			
			if stop == "CP1":
				distance = 23
			elif stop == "CP2":
				distance = 32
			elif stop == "CP3":
				distance = 81
			elif stop == "CP4":
				distance = 115
			elif stop == "CP5":
				distance = 150
			elif stop == "SS1":
				distance = 42
			elif stop == "SS2":
				distance = 71
			elif stop == "SS3":
				distance = 100
			elif stop == "SS4":
				distance = 136
			elif stop == "SS5":
				distance = 166
			elif stop == "SS6":
				distance = 186
			else:
				distance = cts_timeform.cleaned_data['distance']
				stop_name = str(distance) + " miles"
		
			stop_results = {}
			for key in stop_results_dict:
				if key > distance:		
					stop_results[key] = stop_results_dict[key]

			total_delay_mins = 0	
			if distance >= 42:
				total_delay_mins = 10
			if distance >= 71:
				total_delay_mins = 20
			if distance >= 100:
				total_delay_mins = 60
			if distance >= 136:
				total_delay_mins = 70
			if distance >= 166:
				total_delay_mins = 80
			if distance >= 186:
				total_delay_mins = 90

			start_time = datetime.time(hour=4, minute=40)

			elapsed_time = datetime.datetime.combine(datetime.date.today(), stop_time) - datetime.datetime.combine(datetime.date.today(), start_time)		
	#		print(str(elapsed_time))
			moving_time = elapsed_time - datetime.timedelta(minutes=total_delay_mins)
	#		print(str(moving_time))

			speed = round(distance / ((moving_time.seconds / 60) / 60), 1)
	#		print(str(speed))
			slower_speed = round(speed - 1, 0)
			faster_speed = round(speed + 1, 0)

			rows = {}

			for key in stop_results:
				distance_to_travel = key - distance

				time_to_travel_current = datetime.timedelta(hours=(distance_to_travel / speed))		# Hours
				time_to_travel_slower =  datetime.timedelta(hours=(distance_to_travel / slower_speed))	
				time_to_travel_faster =  datetime.timedelta(hours=(distance_to_travel / faster_speed))	

				eta_at_current = datetime.datetime.combine(datetime.date.today(), stop_time) + time_to_travel_current
				eta_at_slower = datetime.datetime.combine(datetime.date.today(), stop_time) + time_to_travel_slower
				eta_at_faster = datetime.datetime.combine(datetime.date.today(), stop_time) + time_to_travel_faster


			#	print("Stop at " + str(key) + " miles = " + str(stop_results_dict[key]))
			#	print("Distance to travel = " + str(distance_to_travel))
			#	print("Time to travel = " + str(time_to_travel_current))
			#	print("ETA = " + str(eta_at_current))
			#	print("")

				rows[key] = {
					'stop': stop_results[key],
					'continue': eta_at_current.time(),
					'slower': eta_at_slower.time(),
					'faster': eta_at_faster.time()}
		
			# print(str(rows))
			results = {'stop': stop_name, 'time': stop_time, 'speed':speed, 'slower_speed':slower_speed, 'faster_speed':faster_speed, 'rows':rows}


			print(str())

		else:
			results = None
	else:
		results = None
		cts_timeform = CTSTime()

	return render(request, "bullets/cts_time.html", {'cts_form':cts_timeform, 'results':results})


### REDIRECT FOR LEADERS APP

def leaders(request):
	return redirect('http://afternoon-beach-6067-148.herokuapp.com/sunlight/leaders/')


## special 404 handler to see what's happening
def error404(request):
	if os.environ.get('LOG_404'):
	# special 404 handler
		print("404 page hit for: " + str(request.build_absolute_uri()))
		if "HTTP_REFERER" in request.META:
			print(" (404 referrer): " + str(request.META["HTTP_REFERER"]))
		print(" (404 GET): " + str(request.GET))
		print(" (404 POST): " + str(request.POST))

	return render(request, "404.html", {}, status=404)




