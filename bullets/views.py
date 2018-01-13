from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import django.core.exceptions
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django.utils import timezone
from django.db.models import Q, Sum
from django.core.urlresolvers import reverse
from django.urls import reverse_lazy

# Python imports 
from datetime import timedelta
import uuid
import random

# Bullets imports
from .forms import RegisterForm, UnRegisterForm, ContactForm, NewsForm, RunningEventForm, BulletEventForm
from .models import Bullet, OldBullet, News, RunningEvent, ActivityCache, BulletEvent

from .utils import send_bullet_mail 

# SALEOR imports
from saleor.core.utils import build_absolute_uri
from saleor.userprofile.models import User

import mailchimp  # for adding users to our mailing list
import logging    # For the logging library

# Get an instance of a logger
logger = logging.getLogger(__name__)



# Decorator style for checking login status
def is_core_team(user):
    return user.groups.filter(name='CoreTeam').exists()


# get list of people to email
def who_to_email():
    return User.objects.filter(groups__name='EmailRecipients').values_list('email', flat=True)



def index(request):
    # Get the cached number of Strava Runners and Cylists
    strava_runners = request.site.settings.runners 
    strava_cyclists = request.site.settings.cyclists

    now = timezone.now()

    week_run_miles =  ActivityCache.objects.filter(activity_type=ActivityCache.RUN).filter(start_date__gte=(now-timedelta(days=7))).aggregate(Sum('distance'))['distance__sum']
    week_ride_miles =  ActivityCache.objects.filter(activity_type=ActivityCache.RIDE).filter(start_date__gte=(now-timedelta(days=7))).aggregate(Sum('distance'))['distance__sum']

    year_run_miles = ActivityCache.objects.filter(activity_type=ActivityCache.RUN).filter(start_date__year=now.year).aggregate(Sum('distance'))['distance__sum']

    year_ride_miles = ActivityCache.objects.filter(activity_type=ActivityCache.RIDE).filter(start_date__year=now.year).aggregate(Sum('distance'))['distance__sum']

    week_runs = ActivityCache.objects.filter(activity_type=ActivityCache.RUN).filter(start_date__gte=(now-timedelta(days=7))).count()
    week_rides = ActivityCache.objects.filter(activity_type=ActivityCache.RIDE).filter(start_date__gte=(now-timedelta(days=7))).count()

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
       


# Handle contact form 
def contact(request): 
	if request.method == 'POST':
        	# create a form instance and populate it with data from the request:
		contact_form = ContactForm(request.POST)
        	# check whether it's valid:
		if contact_form.is_valid():
			context = contact_form.cleaned_data 

			send_bullet_mail(
        			template_name='bullets/contact',
        			recipient_list=who_to_email(),
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


#### CORE TEAM VIEWS ####


### Main page for the core team
@login_required
@user_passes_test(is_core_team, login_url="/") # are they in the core team group?    
def bullets_core_team(request):
    messages.info(request, 'Only members of the core team can view this page!')

    bullets = Bullet.objects.count()

    last_week = timezone.now() - timedelta(days=7)
    last_month = timezone.now() - timedelta(days=30)

    bullets_week = Bullet.objects.filter(date_added__gte=last_week).count()
    bullets_month = Bullet.objects.filter(date_added__gte=last_month).count()

    news_items = News.objects.order_by("-date_added")

    return render(request, "bullets/admin/core_team.html", {'bullets':bullets, 'bullets_week':bullets_week, 'bullets_month':bullets_month, 'news_items':news_items})


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




