from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import django.core.exceptions
from django.conf import settings

from django.core.urlresolvers import reverse
from django.contrib import messages

from .forms import RegisterForm, UnRegisterForm, ContactForm, tdbForm
# UploadCSVForm, VeloForm, VeloRiderForm, VeloRunnerForm, BulletsRunnerForm, tdbForm
from .models import SiteValue, Bullet, OldBullet, News, TdBStage, TdBLeaderBoard_Entry, CTSVehicle, CTSVehiclePosition, CTSRider, CTSRiderPosition
#VeloVolunteer, BulletsRunner,
from saleor.core.utils import build_absolute_uri
 
import mailchimp
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic.list import ListView
from django.utils import timezone
from django.db.models import Q
from saleor.userprofile.models import User

from .utils import send_bullet_mail 
from datetime import timedelta
import uuid

# import the logging library
import logging

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
    strava_runners = SiteValue.objects.get(name=settings.STRAVA_NUM_RUNNERS).value
    strava_cyclists =  SiteValue.objects.get(name=settings.STRAVA_NUM_RIDERS).value

    week_run_miles = SiteValue.objects.get(name=settings.STRAVA_WEEKLY_RUN_MILES).value
    week_ride_miles = SiteValue.objects.get(name=settings.STRAVA_WEEKLY_RIDE_MILES).value

    year_run_miles = SiteValue.objects.get(name=settings.STRAVA_YEAR_RUN_MILES).value
    year_ride_miles = SiteValue.objects.get(name=settings.STRAVA_YEAR_RIDE_MILES).value

    week_runs = SiteValue.objects.get(name=settings.STRAVA_WEEKLY_RUNS).value
    week_rides = SiteValue.objects.get(name=settings.STRAVA_WEEKY_RIDES).value

    year_runs = SiteValue.objects.get(name=settings.STRAVA_YEAR_RUNS).value
    year_rides = SiteValue.objects.get(name=settings.STRAVA_YEAR_RIDES).value

    now = timezone.now()

    qs = News.objects.order_by("-date_added")
    qs = qs.filter(Q(display_after__lte=now) | Q(display_after=None))
    qs = qs.filter(Q(display_until__gte=now) | Q(display_until=None))
    qs = qs.filter(front_page=True)
  
    return render(request, "bullets/index.html", {'strava_runners':strava_runners, 'strava_cyclists':strava_cyclists, 'week_run_miles':week_run_miles, 'week_ride_miles':week_ride_miles,'year_run_miles':year_run_miles, 'year_ride_miles':year_ride_miles, 'week_runs':week_runs, 'week_rides':week_rides, 'year_runs':year_runs, 'year_rides':year_rides, 'news':qs, 'year':now.year})


	

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
                print("This way")
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

    return render(request, "bullets/register.html", {'register_form':register_form})


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
   
    return render(request, "bullets/unregister.html", {'unregister_form':unregister_form})
       


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



#### CORE TEAM VIEWS ####


### Main page for the core team
@login_required
@user_passes_test(is_core_team, login_url="/") # are they in the core team group?     # TODO: this didn't work?
def bullets_core_team(request):
    messages.info(request, 'Only members of the core team can view this page!')

    bullets = Bullet.objects.count()

    last_week = timezone.now() - timedelta(days=7)
    last_month = timezone.now() - timedelta(days=30)

    bullets_week = Bullet.objects.filter(date_added__gte=last_week).count()
    bullets_month = Bullet.objects.filter(date_added__gte=last_month).count()

    news_items = News.objects.order_by("-date_added")

    return render(request, "bullets/admin/core_team.html", {'bullets':bullets, 'bullets_week':bullets_week, 'bullets_month':bullets_month, 'news_items':news_items})




#### BULLETS RUN STUFF ####

from saleor.product.models import ProductVariant
from saleor.cart.utils import get_cart_from_request
from saleor.cart.utils import set_cart_cookie
from django.http import HttpResponseRedirect

def bullets_run_register(request):
	if request.method == 'POST':
        	# create a form instance and populate it with data from the request:
		run_form = BulletsRunnerForm (request.POST)
        	# check whether it's valid:
		if run_form.is_valid():
			# Save the runner in the DB, then direct onwards to the shop
			runner = run_form.save()
			messages.info(request, 'Please complete the checkout process to finish your Bullets Run registration')

			if runner.race == '5':
				v_pk = 373	# variant PK for the 5k run
			else:
				v_pk = 374	# variant PK for the 10k run

			variant = ProductVariant.objects.get(pk=v_pk)	

			cart = get_cart_from_request(request, create=True)
			response = HttpResponseRedirect("/bullets-shop/checkout/")		# to avoid cheeky folk adding multiple tickets
		
			if not request.user.is_authenticated():
               			set_cart_cookie(cart, response)

			cart.add(variant)
			request.session["bulletsRun"] = runner.id
	
			return response	
			
  
	else:
        	run_form = BulletsRunnerForm()
  
	return render(request, "bullets/bullets_run_register.html", {'run_form':run_form})


def bullets_run_reminder(request, uuid):
	runner = get_object_or_404(BulletsRunner, unique_url=uuid)
	
	if runner.paid():
		messages.info(request, 'You have already paid for the Bullets Run!')
		return redirect(reverse('index'))


	messages.info(request, 'Please complete the checkout process to finish your Bullets Run registration')
	if runner.race == '5':
		v_pk = 373	# variant PK for the 5k run
	else:
		v_pk = 374	# variant PK for the 10k run

	variant = ProductVariant.objects.get(pk=v_pk)	

	cart = get_cart_from_request(request, create=True)
	response = HttpResponseRedirect("/bullets-shop/checkout/")		# to avoid cheeky folk adding multiple tickets
		
	if not request.user.is_authenticated():
        	set_cart_cookie(cart, response)

	cart.add(variant, replace=True)
	request.session["bulletsRun"] = runner.id
	
	return response	

	


def bullets_run_stats(request):
	qs = BulletsRunner.objects.filter(order_reference__isnull=False)
	fiveK = qs.filter(race='5').count()
	tenK = qs.filter(race='10').count()
	not_paid = BulletsRunner.objects.filter(order_reference__isnull=True).count()

	return render(request, "bullets/bullets_run_stats.html", {'fiveK':fiveK, 'tenK':tenK, 'not_paid':not_paid})


### LIST ALL THE RUNNERS
@login_required
@user_passes_test(is_core_team, login_url="/") # are they in the core team group?
def bullets_run_admin(request):
	runners = BulletsRunner.objects.all()
	return render(request, "bullets/bullets_run_admin.html", {'runners':runners})



### EDIT RUNNER
@login_required
@user_passes_test(is_core_team, login_url="/") # are they in the core team group?
def bullets_run_admin_edit(request, pk):
	runner = get_object_or_404(BulletsRunner, pk=pk)
	if request.POST:
		run_form = BulletsRunnerForm(request.POST, instance=runner)

		if run_form.is_valid():
			run_form.save()
			messages.success(request, "Saved changes")
			return redirect(reverse('bullets-run-admin'))

	else:
		run_form = BulletsRunnerForm(instance=runner)

	return render(request, "bullets/bullets_run_edit.html", {'run_form':run_form, 'runner':runner})



### DELETE RUNNER
@login_required
@user_passes_test(is_core_team, login_url="/") # are they in the core team group?
def bullets_run_admin_delete(request, pk):
	runner = get_object_or_404(BulletsRunner, pk=pk)
	if request.POST:
		runner.delete()
		messages.success(request, "Runner was deleted!")
		return redirect(reverse('bullets-run-admin'))

	return render(request, "bullets/bullets_run_delete.html", {'runner':runner})



@login_required
@user_passes_test(is_core_team, login_url="/") # are they in the core team group?
def bullets_run_offline(request):
	run_form = BulletsRunnerForm()

	if request.method == 'POST':
        	# create a form instance and populate it with data from the request:
		new_run_form = BulletsRunnerForm (request.POST)
        	# check whether it's valid:
		if new_run_form.is_valid():
			# Save the runner in the DB, then direct onwards to the shop
			runner = new_run_form.save()
			runner.paid_offline = True
			runner.save()

			messages.success(request, "Have registered " + runner.name + " for the Bullets run")
		else:
			messages.error(request, "There is a problem in the information you supplied")

			run_form = new_run_form		# get the errors to the page if it didn't work
           	  
	return render(request, "bullets/bullets_run_edit.html", {'run_form':run_form})

	




#### VELO STUFF BELOW HERE #####

#def velo(request): 
#	if request.method == 'POST':
#        	# create a form instance and populate it with data from the request:
#        	velo_form = VeloForm(request.POST)
#        	# check whether it's valid:
#        	if velo_form.is_valid():
#			if (velo_form.cleaned_data["volunteer_type"] == VeloForm.RIDER):
#				# if they're a rider, they've got to be a bullet
#				bullets = Bullet.objects.filter(email__iexact=velo_form.cleaned_data['email'])
#				if bullets.count() == 0:
#					# Not registered
#					 return render(request, "bullets/velo_problem.html", {})
#				else:
#					bullet = bullets[0]	# not ideal, but what are you going to do?
#					# now, which type of volunteering are they doing?
#					rider_form = VeloRiderForm()
#					return render(request, "bullets/velo_rider.html", {'velo_rider_form':rider_form, 'bullet':bullet})
#			else:
#				nonrider_form = VeloRunnerForm()
#				return render(request, "bullets/velo_nonrider.html", {'velo_nonrider_form':nonrider_form, 'email':velo_form.cleaned_data['email']})		
#  
#   	else:
#        	velo_form = VeloForm()
#  
#        return render(request, "bullets/velo.html", {'velo_form':velo_form})


#def send_velo_email(volunteer):
#	url = reverse('velo-details', args=[volunteer.unique_ref])
#	url = build_absolute_uri(url)
#
#	context = {}
#
#	context['volunteer'] = volunteer
#	context['url'] = url
#
#	emailit.api.send_mail(context=context, recipients=volunteer.get_email(), template_base='email/velo', from_email="leaders@boldmerebullets.com")
#
#	return


# TODO: refactor below two functions to be one?
#def velo_rider(request):
#	if request.method == 'POST':
#		rider_form = VeloRiderForm(request.POST)
#		if rider_form.is_valid():
#			bullet_id = request.POST.get("bullet")
#			bullet = get_object_or_404(Bullet, pk=bullet_id)
#			
#			# got here = all good for creating a velo volunteer!
#			
#			volunteer, created = VeloVolunteer.objects.get_or_create(bullet=bullet, defaults={'address':rider_form.cleaned_data["address"], 'volunteer_type':VeloVolunteer.RIDER, 'entered_velo':rider_form.cleaned_data["entered_velo"], 'average_speed':rider_form.cleaned_data["average_speed"], 'jersey_size':rider_form.cleaned_data["jersey_size"], 'short_size':rider_form.cleaned_data["short_size"], 'drive_van':False, 'contact_no':"-", 'drive_bus':False, 'kit_sex':rider_form.cleaned_data["kit_sex"]})
#			
#			if created:
#				send_velo_email(volunteer)
#				messages.success(request, 'You have successfully signed up to volunteer at the Velo!');
#		
#			else:
#				messages.info(request, 'It looks like you have previously signed up!');
#			
#			return render(request, "bullets/velo_thanks.html", {'volunteer':volunteer})
#	
#	messages.info(request, 'Something went wrong - please try again?')
#	return redirect(reverse('velo'))
#
			

#def velo_nonrider(request):
#	if request.method == 'POST':
#		runner_form = VeloRunnerForm(request.POST)
#		if runner_form.is_valid():
#			email_address = request.POST.get("email")
#					
#			# got here = all good for creating a velo volunteer!
#			
#			volunteer, created = VeloVolunteer.objects.get_or_create(email=email_address, defaults={'name':runner_form.cleaned_data['name'], 'address':runner_form.cleaned_data["address"], 'volunteer_type':VeloVolunteer.NON_RIDER, 'tshirt_size':runner_form.cleaned_data["tshirt_size"], 'drive_van': runner_form.cleaned_data["drive_van"], 'contact_no':runner_form.cleaned_data['contact_no'], 'drive_bus':runner_form.cleaned_data["drive_bus"], 'entered_velo':False})
#
#			
#			if created:
#				send_velo_email(volunteer)
#				messages.success(request, 'You have successfully signed up to volunteer at the Velo!');
#		
#			else:
#				messages.info(request, 'It looks like you have previously signed up!');
#			
#			return render(request, "bullets/velo_thanks.html", {'volunteer':volunteer})
#	
#	messages.info(request, 'Something went wrong - please try again?')
#	return redirect(reverse('velo'))
#
#
#
#def velo_details(request, uuid):
#	volunteer = get_object_or_404(VeloVolunteer, unique_ref=uuid)
#	if volunteer.volunteer_type == 'r':
#		volunteer_form = VeloRiderForm(request.POST or None, initial={'address': volunteer.address, 'entered_velo':volunteer.entered_velo, 'average_speed':volunteer.average_speed, 'kit_sex':volunteer.kit_sex, 'jersey_size':volunteer.jersey_size, 'short_size':volunteer.short_size, 'contact_no':volunteer.contact_no})
#	else:
#		volunteer_form = VeloRunnerForm(request.POST or None, initial={'name':volunteer.get_name(), 'address': volunteer.address, 'tshirt_size':volunteer.tshirt_size, 'drive_van':volunteer.drive_van, 'drive_bus':volunteer.drive_bus, 'contact_no':volunteer.contact_no})
#
#	if request.method == 'POST':
#		if volunteer.volunteer_type == 'r':
#			if volunteer_form.is_valid():
#				volunteer.address = volunteer_form.cleaned_data['address']
#				volunteer.entered_velo = volunteer_form.cleaned_data['entered_velo']
#				volunteer.average_speed = volunteer_form.cleaned_data['average_speed']
#				volunteer.kit_sex = volunteer_form.cleaned_data['kit_sex']
#				volunteer.jersey_size = volunteer_form.cleaned_data['jersey_size']
#				volunteer.short_size = volunteer_form.cleaned_data['short_size']
#				volunteer.save()
#				messages.success(request, 'Your changes were saved!')
#			else:
#				messages.info(request, "Something went wrong!")
#		else:
#			if volunteer_form.is_valid():
#			#	volunteer.name = volunteer_form.cleaned_data['name']	
#				volunteer.address = volunteer_form.cleaned_data['address']
#				volunteer.tshirt_size = volunteer_form.cleaned_data['tshirt_size']
#				volunteer.drive_van = volunteer_form.cleaned_data['drive_van']
#				volunteer.drive_bus = volunteer_form.cleaned_data['drive_bus']
#				volunteer.contact_no = volunteer_form.cleaned_data['contact_no']
#				volunteer.save()
#				messages.success(request, 'Your changes were saved!')
#			else:
#				messages.info(request, "Something went wrong!")
#				print volunteer_form
#	
#	return render(request, "bullets/velo_details.html", {'volunteer':volunteer, 'volunteer_form':volunteer_form})


#def velo_delete(request):
#	if request.method == 'POST':
#		x = request.POST.get("volunteer")
#		volunteer = get_object_or_404(VeloVolunteer, pk=x)
#		volunteer.delete()
#			
#		messages.info(request, 'Your entry has been deleted')
#	
#	return redirect(reverse('index'))


#def velo_stats(request):
#	riders = VeloVolunteer.objects.filter(volunteer_type='r').count()
#	non_riders = VeloVolunteer.objects.filter(volunteer_type='n').count()
#
#	return render(request, "bullets/velo_stats.html", {'riders':riders, 'non_riders':non_riders})


#@login_required
#@user_passes_test(is_core_team, login_url="/") # are they in the core team group?
#def velo_admin(request):  ## View for Kate + Lisa
#	messages.info(request, 'Only members of the core team can view this page!')
#
#	riders = VeloVolunteer.objects.filter(volunteer_type='r')
#	non_riders = VeloVolunteer.objects.filter(volunteer_type='n')
#
#	return render(request, "bullets/velo_admin.html", {'riders':riders, 'non_riders':non_riders})
#

#@login_required
#@user_passes_test(is_core_team, login_url="/") # are they in the core team group?
#def velo_admin_delete(request, pk):  		## View for Kate + Lisa
#
#	volunteer = get_object_or_404(VeloVolunteer, pk=pk)
#	if request.POST:
#		volunteer.delete()
#		messages.success(request, "Volunteer was deleted!")
#		return redirect(reverse('velo-admin'))
#
#	return render(request, "bullets/velo_admin_delete.html", {'volunteer':volunteer})
#

#@login_required
#@user_passes_test(is_core_team, login_url="/") # are they in the core team group?	
#def velo_admin_email(request):
#	volunteers = VeloVolunteer.objects.filter(volunteer_type='n')
#
#	if request.POST:
#		x = 0
#		# actually send email
#		for volunteer in volunteers:
#			url = reverse('velo-details', args=[volunteer.unique_ref])
#			url = build_absolute_uri(url)
#
#			context = {}
#
#			context['volunteer'] = volunteer
#			context['url'] = url
#
#			emailit.api.send_mail(context=context, recipients=volunteer.get_email(), template_base='email/velo_nonride_reminder', from_email="Kate <kate@boldmerebullets.com>")
#			x = x + 1
#
#		messages.success(request, "Sent " + str(x) + " emails!")
#		return redirect(reverse('velo-admin'))
#	else:
#		return render(request, "bullets/velo_admin_email.html", {'volunteers':volunteers})
#		
#

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
	


#### Tour de Boldmere views

def tdb(request):
	now = timezone.now()
#	stages = TdBStage.objects.filter(valid_from__lte=now, valid_until__gte=now)
	stages = TdBStage.objects.all().order_by('id')

	r = []
	show_results = False
	for s in stages:
		a = {'id':s.id, 'name':s.name, 'show_details':s.show_details(), 'stage_type': s.stage_type, 'valid_from':s.valid_from, 'how_many_completed': s.how_many_completed()}
		r.append(a)

	if request.method == 'POST':
		form = tdbForm(request.POST)
		if form.is_valid():
			show_results = True
			r = []
			for s in stages:
				a = {'id':s.id, 'show_details':s.show_details(), 'stage_type':s.stage_type, 'valid_from':s.valid_from, 'name':s.name, 'how_many_completed': s.how_many_completed(), 'done_stage':s.athlete_done_stage(form.cleaned_data['strava_id'])}
				r.append(a)
			
	else:
		form = tdbForm()

	return render(request, "bullets/tdb.html", {'stages':r, 'tdb_form':form, 'show_results':show_results})


def tdbStage(request, pk):
	stage = get_object_or_404(TdBStage, pk=pk)	
	return render(request, "bullets/tdbStage.html", {'stage':stage})



def add_to_leaderboard(leaderboard, entries, stage_id):
	# dict {athlete: total time}   entries=  qs
	for entry in entries.all():
		if entry.athlete_id in leaderboard:
			x = leaderboard[entry.athlete_id]
			timetaken = x[0] + entry.time_taken
			stages_complete = x[1]
			if stage_id not in stages_complete:
				stages_complete.append(stage_id)
		else:
			timetaken = entry.time_taken
			stages_complete = 1
			stages_complete = [stage_id]
	
		leaderboard[entry.athlete_id] = (timetaken, stages_complete, entry.athlete_name)
				
import operator
def tdbLeaderBoard(request):
	stages = TdBStage.objects.all().order_by('id')

	hill_times = {}
	flat_times = {}
#	overall_times = {}
	qualifying_times = {}
	
	hilly_stages = 0
	flat_stages = 0
	yellow_stages = 0
	yellow_jersey_times = {}

	
	for stage in stages:
		print("working out leaderboard for " + str(stage) + " ID = " + str(stage.id))
		added_stage = False
		if stage.hilly_segment:
			add_to_leaderboard(hill_times, stage.hilly_leaderboard(), stage.id)
			add_to_leaderboard(yellow_jersey_times, stage.hilly_leaderboard(), stage.id)

			hilly_stages = hilly_stages + 1
			added_stage = True

		if stage.flat_segment:
			add_to_leaderboard(flat_times, stage.flat_leaderboard(), stage.id)
			add_to_leaderboard(yellow_jersey_times, stage.flat_leaderboard(), stage.id)
			flat_stages = flat_stages + 1
			added_stage = True
	
#		if stage.overall_segment:
#			add_to_leaderboard(overall_times, stage.overall_leaderboard(), stage.id)	# might be empty?
#			add_to_leaderboard(yellow_jersey_times, stage.overall_leaderboard(), stage.id)
#			added_stage = True

		if stage.id == 3:
			add_to_leaderboard(qualifying_times, stage.overall_leaderboard(), stage.id)
			
		
		if added_stage:
			yellow_stages = yellow_stages + 1

	yellow_jersey_times_a = {}
	hill_times_a = {}
	flat_times_a = {}

	for athlete_id, (timetaken, stages_complete, athlete_name) in yellow_jersey_times.iteritems():
		if athlete_id in qualifying_times:
			yellow_jersey_times_a[athlete_id] = (timetaken, len(stages_complete), athlete_name)

	for athlete_id, (timetaken, stages_complete, athlete_name) in hill_times.iteritems():
		if athlete_id in qualifying_times:
			hill_times_a[athlete_id] = (timetaken, len(stages_complete), athlete_name)

	for athlete_id, (timetaken, stages_complete, athlete_name) in flat_times.iteritems():
		if athlete_id in qualifying_times:
			flat_times_a[athlete_id] = (timetaken, len(stages_complete), athlete_name)




	sorted_hill_times = sorted(hill_times_a.items(), key=operator.itemgetter(1))		# Polka dot
	sorted_flat_times = sorted(flat_times_a.items(), key=operator.itemgetter(1))		# Green
#	sorted_overall_times = sorted(overall_times.items(), key=operator.itemgetter(1))

	sorted_yellow_times =  sorted(yellow_jersey_times_a.items(), key=operator.itemgetter(1))

#	print sorted_yellow_times

#	print sorted_hill_times


	return render(request, "bullets/tdbLeaderboard.html", {'green':sorted_flat_times, 'polka':sorted_hill_times, 'yellow':sorted_yellow_times, 'yellow_stages':yellow_stages, 'green_stages': flat_stages, 'polka_stages':hilly_stages})




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


### SPECIAL PAGES - CERTBOT


#import os

#def CertBot(request, part1):
#	print "Part1"
#	print str(part1)
#	part2 = os.environ.get('CERTBOT_PART2')
#	print "Part2"
#	print str(part2)
#	x = str(part1) + "." + str(part2)
#	print x
#	return HttpResponse(x)
















##########################################
## One off URLs stuff for member upload ##
##########################################


#def upload_member_csv(request):
#    if request.method == 'POST':
#        form = UploadCSVForm(request.POST, request.FILES)i
#	print "came this way"
#	print "form = " + str(form)
 #       if form.is_valid():
 #           bullets_list = handle_uploaded_file(request.FILES['csv_file']) 
#	    
 #           return render(request, 'bullets/upload-csv-part2.html', {'bullets_list':bullets_list})
 #   else:
 #       form = UploadCSVForm()
#    return render(request, 'bullets/upload-csv.html', {'form': form})

#import sys
#from storages.backends.s3boto import S3BotoStorage
#from django.conf import settings
#import pickle

#class CSVStorage(S3BotoStorage):
#	bucket_name = settings.CSVFILE_BUCKET_NAME
#	location = settings.CSVFILE_LOCATION
#	default_acl = 'private'



#def handle_uploaded_file(csvfile):
#
#	csvreader = UnicodeReader(csvfile, delimiter=',', quotechar='"')
#	count = 0
#	bullets_list = []
# 0"date joined", 1"first name", 2"surname", 3"post-code", 4"contact number", 5"email", 6"contactable?". 	
#	for row in csvreader:
#		print "Here we go: " + str(row)
#		name = row[1] + u' ' + row[2]
#		postcode = row[3][0:4]
#		email = row[5]
#		contact_no = row[4]
#		joined_date = dateutil.parser.parse(row[0])
#		print "joined date = " 
#		print joined_date
#
#		get_emails = (row[6] == 'Yes')
#		
#		bullet = {'name':name, 'postcode':postcode, 'email':email, 'contact_no':contact_no, 'over_18':True, 'joined':joined_date, 'get_emails':get_emails, 'email_checked':True}
#		bullets_list.append(bullet)
#
#	x = CSVStorage()
#	backupfile = x.open("bullets.pickle", "wb")
#	pickle.dump(bullets_list, backupfile)	
#	backupfile.close()
#
#	print ""
#	print "added " + str(count)
#	return bullets_list
 #  

#def upload_member_csv_part2(request):
#	messages.success(request, 'Thanks to your engagement, I added the bullets to the DB');
#
#	return redirect(reverse('index'))


#import csv, codecs, cStringIO
#
#import dateutil.parser
#
#
#class UTF8Recoder:
#    """
#    Iterator that reads an encoded stream and reencodes the input to UTF-8
#    """
#    def __init__(self, f, encoding):
#        self.reader = codecs.getreader(encoding)(f)
#
#    def __iter__(self):
#        return self
#
#    def next(self):
#        return self.reader.next().encode("utf-8")
#
#class UnicodeReader:
#    """
#    A CSV reader which will iterate over lines in the CSV file "f",
#    which is encoded in the given encoding.
#    """
#
#    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
#        f = UTF8Recoder(f, encoding)
#        self.reader = csv.reader(f, dialect=dialect, **kwds)
#
#    def next(self):
#        row = self.reader.next()
#        return [unicode(s, "utf-8") for s in row]
#
#    def __iter__(self):
#        return self






### NOTE: client side always uses Vehicle.number (not PK) to reference the vehicles - we have to translate at this end

def cts_mobile(request):
	if request.method == 'POST':
		vehicle_id = request.POST.get('select-car', 0)

		vehicle = get_object_or_404(CTSVehicle, pk=vehicle_id)
		
		request.session['vehicle_id'] = vehicle.id
#		print vehicle.id

#		request.session['name'] = request.POST.get('your-name', 'default')		
		return redirect(reverse('cts-mobile-menu'))

	else:
		vehicles=CTSVehicle.objects.all()	
		return render(request, "bullets/cts/start.html", {'vehicles':vehicles})



def cts_mobile_menu(request):
	x = request.session.get('vehicle_id', 0)
#	print x
	if (x == 0):
		return redirect(reverse('cts-mobile'))
	else:
		vehicle = get_object_or_404(CTSVehicle, pk=x)
#		print vehicle

		vehicles=CTSVehicle.objects.all()

		return render(request, "bullets/cts/menu.html", {'vehicles':vehicles, 'vehicle':vehicle})



def cts_mobile_map(request, pk=0):
	x = request.session.get('vehicle_id', 0)
	if (x == 0):
		return redirect(reverse('cts-mobile'))
	else:
		vehicle = get_object_or_404(CTSVehicle, pk=x)
		vehicles=CTSVehicle.objects.all()

		centre_on = None
		if (pk != 0):
			centre_on = get_object_or_404(CTSVehicle, pk=pk)

		return render(request, "bullets/cts/map.html", {'vehicles':vehicles, 'vehicle':vehicle, 'centre_on':centre_on})


def cts_mobile_vehicle_list(request):
	x = request.session.get('vehicle_id', 0)
	if (x == 0):
		return redirect(reverse('cts-mobile'))
	else:
		vehicle = get_object_or_404(CTSVehicle, pk=x)
		vehicles=CTSVehicle.objects.all()

		return render(request, "bullets/cts/list.html", {'vehicles':vehicles, 'vehicle':vehicle})


def cts_mobile_support_stop(request):		
	x = request.session.get('vehicle_id', 0)
	if (x == 0):
		return redirect(reverse('cts-mobile'))
	else:
		vehicle = get_object_or_404(CTSVehicle, pk=x)
		vehicles=CTSVehicle.objects.all()

		return render(request, "bullets/cts/stop.html", {'vehicles':vehicles, 'vehicle':vehicle})



def cts_mobile_rider_positions(request):
	x = request.session.get('vehicle_id', 0)
	if (x == 0):
		return redirect(reverse('cts-mobile'))
	else:
		return render(request, "bullets/cts/rider-positions.html", {})



def cts_big_map(request):
	return render(request, "bullets/cts/rider-map.html", {})

def cts_mobile_logout(request):
	del request.session['vehicle_id']
	request.session.modified = True 
	return redirect(reverse('cts-mobile'))


#    url(r'^cts-mobile/menu/$', views.cts_mobile_menu, name='cts-mobile-menu'),
#    url(r'^cts-mobile/map/$', views.cts_mobile_map, name='cts-mobile-map'),
#    url(r'^cts-mobile/vehicle_list/$', views.cts_mobile_vehicle_list, name='cts-mobile-vehicle-list'),
#    url(r'^cts-mobile/support-stop/$', views.cts_mobile_support_stop, name='cts-mobile-support-stop'),
#    url(r'^cts-mobile/rider-positions/$', views.cts_mobile_rider_positions, name='cts-mobile-rider-positions'),
#    url(r'^cts-mobile/where-to-now/$', views.cts_mobile_where_to, name='cts-mobile-where-to'),



from django.http import JsonResponse
import json
import datetime
from django.core.exceptions import ObjectDoesNotExist 

def cts_vehicle_position_ajax(request):
	# get sent the car's current location; send back everyone else's latest spot
	# get from AJAX which car and where it is

	if request.method == 'POST':
		#print request.body
		from_client = json.loads(request.body)	
	#	print from_client

		vehicle_id = from_client["vehicleID"]	# remember, this is the wrong one - convert to a PK
	#	myName = from_client["name"]
		lat= from_client["lat"]
		lon= from_client["lon"]
		jsts = from_client["timestamp"]

		dt = datetime.datetime.fromtimestamp(jsts/1000.0)

		vehicle = CTSVehicle.objects.get(number=vehicle_id)
#		vehicle.name = myName
#		vehicle.save()

		cvp = CTSVehiclePosition(vehicle=vehicle, lat=lat, lon=lon, timestamp=dt)	# No chance!
		cvp.save()


	cars = CTSVehicle.objects.exclude(number=vehicle_id) 	# filter out this one?
	latest_positions = {}
	for car in cars:
		try:
			x = car.get_latest_position()
			r = {'vehicleID':car.number, 'name':car.name, 'lat':x.lat, 'lon':x.lon, 'timestamp':x.timestamp}		# TODO: add in whether car is at a support stop
			latest_positions[car.number] = r

		except ObjectDoesNotExist:
			pass	
#	data = {'2': (52.8344318,-1.8217034), '3': (52.6280446,-1.7220216)}

	return JsonResponse(latest_positions)



def cts_rider_position_ajax(request):
	riders = CTSRider.objects.all()
	latest_positions = {}
	for rider in riders:
		try:
			x = rider.get_latest_position()
			y = CTSRiderPosition.objects.filter(rider=rider)
			old_positions = []
			for old_pos in y:
				a = {'timestamp':old_pos.timestamp, 'distance':old_pos.distance_from_start}
				old_positions.append(a)
			
			r = {'riderID':rider.id, 'name':rider.name, 'lat':x.lat, 'lon':x.lon, 'distance':x.distance_from_start, 'timestamp': x.timestamp, 'old_positions':old_positions}
			
			latest_positions[rider.id] = r

		except ObjectDoesNotExist:
			now = timezone.now()
			r = {'riderID':rider.id, 'name':rider.name, 'lat': 51.4401081, 'lon':0.7788546, 'distance': 0, 'timestamp': now, 'old_positions':[]}
			latest_positions[rider.id] = r


	return JsonResponse(latest_positions)



def cts_rider_checkin_ajax(request):
	# rider has been checked in at a support stop
		#print request.body
	from_client = json.loads(request.body)	
	#	print from_client

	rider_id = from_client["riderID"]	# remember, this is the wrong one - convert to a PK
	lat= from_client["lat"]
	lon= from_client["lon"]
	jsts = from_client["timestamp"]
	distance = from_client["distance"]
	delete_mode = from_client["delete_mode"]
	if (delete_mode):
		crpID = from_client["crpID"]
		crp = get_object_or_404(CTSRiderPosition, pk=crpID)
		crp.delete()
		response = {'jobDone':True}
		print("deleted " + str(crpID))

	else:
		dt = datetime.datetime.fromtimestamp(jsts/1000.0)
		rider = CTSRider.objects.get(pk=rider_id)

		crp = CTSRiderPosition(rider=rider, lat=lat, lon=lon, timestamp=dt, distance_from_start=distance)	# No chance!
		crp.save()

		response = {'crpID':crp.id}

	return JsonResponse(response)


