from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import smart_text, python_2_unicode_compatible
from autoslug import AutoSlugField
from django.urls import reverse
import uuid
from .utils import send_bullet_mail
from django.utils import timezone
import datetime


# This model holds a minimised cache of every strava activity we've seen from the club members
class ActivityCache(models.Model):
    RUN = 'run'
    RIDE = 'ride'

    ACTIVITY_TYPE_CHOICES = (
        (RUN, 'Run'),
        (RIDE, 'Ride'),
        )

    activity_id = models.CharField('Strava ID', max_length=30)
    activity_type = models.CharField('Type',
        max_length=4,
        choices=ACTIVITY_TYPE_CHOICES,
        default=RIDE,
        )
    distance = models.PositiveIntegerField('Distance')
    start_date = models.DateTimeField('Activity Date')



class Person(models.Model):
    name = models.CharField("name", max_length=200)
    email = models.EmailField('email address', max_length=200)
    date_added = models.DateField("date created", auto_now_add=True)
    email_checked = models.DateField("date email confirmed", blank=True, null=True)
    email_check_ref = models.UUIDField("random uuid for email confirmation", default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return smart_text(self.name)

    # when the email address associated with this person is confirmed
    def confirm_email(self):   
        self.email_checked = timezone.now()
        self.email_check_ref = uuid.uuid4() 
        self.save()
  
    
    # Send an email to this person 
    def send_email(self, template, context, dryrun=False, from_email=None, override_email_safety=False, extra_headers={}):
        if self.email_checked == None and override_email_safety == False:
            print("!!! Not emailing " + smart_text(self.name) + "(" + smart_text(self.email) + ") !!!")
            return False

        if dryrun:
            print("*** Would email " + smart_text(self.name) + "("+smart_text(self.email) + ") ***")
            return False
        else:
            send_bullet_mail(template_name=template, recipient_list=[self.email], context=context, extra_headers=extra_headers, from_email=from_email)
            print("Sent an email to " + smart_text(self.email) + " using template " + str(template))
            return True





# this is the registration database
class Bullet(Person):
    postcode = models.CharField('first part of postcode', max_length=5)	
    contact_no = models.CharField('contact number', max_length=100)
    over_18 = models.BooleanField('over 18', help_text='Please confirm that you are over 18?')
    get_emails = models.BooleanField("happy to receive emails", help_text='Can we contact you regarding Collective events?')

    voting_ref = models.UUIDField("random uuid for voting", default=uuid.uuid4, editable=False, blank=True, null=True)		# URL for charity of the year 2017

    def send_charity_email(self, dryrun=False):
        if (self.voting_ref != None):
            url = 'https://www.boldmerebullets.com/charity-vote/vote/' + str(self.voting_ref)
            ctx = {'bullet':self, 'email_url':url}

            return self.send_email(template="bullets/charity_vote", context=ctx, dryrun=dryrun)
        else:
            return False



# this is the registration database
@python_2_unicode_compatible
class OldBullet(models.Model):
	name = models.CharField("name", max_length=200)
	postcode = models.CharField('first part of postcode', max_length=5)
	email = models.EmailField('email address', max_length=200)
	contact_no = models.CharField('contact number', max_length=100)
	over_18 = models.BooleanField('over 18', help_text='Please confirm that you are over 18?')
	get_emails = models.BooleanField("happy to receive emails", help_text='Can we contact you regarding Collective events?')
	joined = models.DateField("date joined", auto_now_add=True)
	email_checked = models.BooleanField('confirmed email', default=False)
	email_check_ref = models.UUIDField("random uuid for email confirmation", default=uuid.uuid4, editable=False)
        
	voting_ref = models.UUIDField("random uuid for voting", default=uuid.uuid4, editable=False, blank=True, null=True)		# URL for charity of the year 2017


	class Meta:
		ordering = ['name']

	def __str__(self):
		return smart_text(self.name)




# News articles on the Bullets site
class News(models.Model):
	title = models.CharField("title", max_length=100)
	extra_title = models.CharField("extra title text (not in link)", max_length=100, blank=True, null=True)
	slug = AutoSlugField(populate_from='title', editable=False)
	redirect_to = models.URLField("redirection story - where to go?", help_text="If you put a website address in here, then don't include a story below; the news story will just redirect to this link", blank=True, null=True)
	story = models.TextField("story", blank=True, null=True)

	date_added = models.DateField("date added", auto_now_add=True)
	display_after = models.DateField("publish on", default=datetime.date.today)
	display_until = models.DateField("remove from site on", blank=True, null=True)
	front_page = models.BooleanField('feature on front page', default=False)

	def __str__(self):	
		if self.extra_title:
			return str(self.title) + " - " + str(self.extra_title)
		else:
        		return str(self.title)

	class Meta:
		verbose_name = "news story"
		verbose_name_plural = "news stories"

	def get_absolute_url(self):
        	return reverse('news-item', kwargs={'slug': self.slug})



## for the Runs on Tuesdays 
@python_2_unicode_compatible
class RunningEvent(models.Model):
	date = models.DateField('Run Date')
	session_type = models.CharField('Session type', max_length=200, blank=True)
	session_details = models.CharField('Session details', max_length=200, blank=False)

	HARVESTER = 'h'
	BOLDMERE = 'b'
	BLACKROOT = 'r'
	
	MEETING_CHOICES = (
		(HARVESTER, 'Harvester'),
		(BOLDMERE, 'Boldmere Gate'),
		(BLACKROOT, 'Blackroot Bistro'),
	)

	meeting_point = models.CharField('Meeting point', max_length=1, choices=MEETING_CHOICES, default=HARVESTER)

	class Meta:
		ordering = ['date']

	def __str__(self):
		return smart_text("Run on " + str(self.date))


@python_2_unicode_compatible
class BulletEvent(models.Model):
    date = models.DateField("Event Date")
    name = models.CharField('Event Name', max_length=200, blank=True)
    link = models.URLField("Link to more info", help_text="If you put a web address in here then we add a link to the events page", blank=True, null=True)

    running_event = models.BooleanField("Running Event", default=False)
    cycling_event = models.BooleanField("Cycling Event", default=False)
    social_event = models.BooleanField("Social Event", default=False)


    def __str__(self):
        return smart_text(self.name)



# For the Womens' Ride
class IWDRider(Person):
    club = models.CharField("Usual club", max_length=200, blank=True)

    NO = 'n'
    SLOWEST = 'a'
    SLOW = 'b'
    MEDIUM = 'c'
    FAST = 'd' 
    FASTEST = 'e'

    SPEED_CHOICES = (
        (NO, 'I do not wish to take part in the ride'),
	(SLOWEST, '10-11mph'),
	(SLOW, '12-13mph'),
        (MEDIUM, '14-15mph'),
        (FAST, '16-17mph'), 
        (FASTEST, '18+mph'),
    )
    
    evans = models.BooleanField("Evans Event?", help_text="Check this box if you'd like to take part in the bike maintenance event at Evans", default=True)
    speed = models.CharField("Women's Ride?", help_text="What speed would you like to do the ride at?", max_length=1, choices=SPEED_CHOICES, default=NO)

    def doing_ride(self):
        return (self.speed != self.NO)





from stravalib import Client

class BigBulletRider(Person):
    # need to cache strava API token
    access_token = models.CharField("Strava access token", max_length=500)
    # TODO: might need a mileometer field here - need to think about how to capture the data without hitting Strava for every page load - regenerate every ten mins maybe?
    # TODO: maybe a manual entry mileage figure? Or just the one - if you've got it from Strava or from a manual entry.

    SHORT = 's'
    MED = 'm'
    LONG = 'l'
    VERYLONG = 'v'
    
    DISTANCE_CHOICES = (
        (SHORT, '50km'),
        (MED, '100km'),
        (LONG, '150km'),
        (VERYLONG, '200km'),
    )

    distance = models.CharField("Which distance would you like to ride?", help_text="Please indicate which distance you would like to ride - you can change on the day!", max_length=1, choices=DISTANCE_CHOICES, default=SHORT)

    def delete(self, *args, **kwargs):
        # deauth from Strava if registered there
        if self.access_token != "":
            client = Client(access_token=self.access_token)
            client.deauthorize()
            self.access_token = ""

        super().delete(*args, **kwargs)




class FredRider(Person):
    # need to cache strava API token
    access_token = models.CharField("Strava access token", max_length=500)
    checked_upto_date = models.DateTimeField('Checked up to', null=True, blank=True)
    def delete(self, *args, **kwargs):
        # deauth from Strava if registered there
        if self.access_token != "":
            client = Client(access_token=self.access_token)
            client.deauthorize()
            self.access_token = ""

        super().delete(*args, **kwargs)


class FredLeaderBoard(models.Model):
    rider = models.ForeignKey(FredRider, on_delete=models.CASCADE)
    strava_activity_id = models.CharField("Strava Activity ID", max_length=50)
    distance = models.PositiveIntegerField('Distance')
    elevation = models.FloatField('Elevation')
    start_date = models.DateTimeField('Activity Date')

    ratio = models.FloatField("elevation per mile")

    def save(self, *args, **kwargs):
        self.ratio = (self.elevation / self.distance)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.rider) + " rode " + str(self.distance) + "miles with " + str(self.elevation) + "m climbing"

   
class FredHighLeaderBoard(FredLeaderBoard):
    class Meta:
        ordering = ['-elevation']


class FredLowLeaderBoard(FredLeaderBoard):
    class Meta:
        ordering = ['ratio']

     


################
## OLD MODELS ##
################
#
#class CharityOfYear(models.Model):
#	name = models.CharField("name", max_length=200)
#	link = models.URLField("link to charity")
#	count = models.PositiveSmallIntegerField('vote count', default=0)
#
#	def __str__(self):
#		return smart_text(self.name)
#
#
#
#
## for the Interclub Ride
#@python_2_unicode_compatible
#class InterclubRider(models.Model):
#	name = models.CharField('name', max_length=200, blank=False) 
#	email =  models.EmailField('email address', max_length=200, blank=False)	
#
#	CLUB_CTC = 'ctc'
#	CLUB_GIRO = 'giro'
#	CLUB_BIRCHFIELD = 'birc'
#	CLUB_PATHFINDERS = 'path'
#	CLUB_BROTHERS = 'bob'
#	CLUB_BULLETS = 'bull'
#	CLUB_MOSELEY = 'mose'
#	CLUB_GORILLA = 'gori'
#	CLUB_TAMWORTH = 'tamw'
#	CLUB_DYNAMIC = 'dyna'
#	CLUB_GREATBARR = 'grbr'
#	CLUB_BRUM = 'brum'
#	CLUB_TRMCC = 'tmcc'
#	CLUB_TITANS = 'tita'
#	CLUB_BREEZE = 'brez'
#	CLUB_CANNON = 'cano'
#	
#
#	CLUB_CHOICES = (
#		(CLUB_BIRCHFIELD, 'Birchfield'),
#		(CLUB_BRUM, 'Birmingham Easy Riders'),
#		(CLUB_BULLETS, 'Boldmere Bullets'),
#		(CLUB_BREEZE, 'Breeze Riders'),
#		(CLUB_BROTHERS, 'Brothers on Bikes'),
#		(CLUB_CANNON, 'Cannon Hill CC'),
#		(CLUB_CTC, 'CTC'),
#		(CLUB_DYNAMIC, 'Dynamic Rides'),
#		(CLUB_GIRO, 'GIRO'),
#		(CLUB_GORILLA, 'Gorilla Coffee Cycling'),
#		(CLUB_GREATBARR, 'Great Barr and Erdingtion Cycling Club'),
#		(CLUB_MOSELEY, 'Moseley Missiles'), 
#		(CLUB_PATHFINDERS, 'Pathfinders'),
#		(CLUB_TAMWORTH, 'Tamworth Cycling Club'),
#		(CLUB_TRMCC, 'Tamworth RMCC'),
#		(CLUB_TITANS, 'Tamworth Titans'),
#		
#	)
#
#	club = models.CharField('club', max_length=4, help_text="Which club do you normally ride with?", choices=CLUB_CHOICES, default=CLUB_BIRCHFIELD)
#	ice = models.CharField('emergency contact number', max_length=200, blank=True) 
#
#	LESIURE = 'les'
#	SOCIAL = 'soc'
#	MEDIUM = 'med'
#	FAST = 'fas'
#	
#	SPEED_TYPE_CHOICES = (
#		(LESIURE, 'Lesiure (10/11/12mph - 19 miles)'),
#		(SOCIAL, 'Social (13/14mph - 30 miles)'),
#		(MEDIUM, 'Medium (15/16/17mph - 39 miles)'),
#		(FAST, 'Long (18/19/20+mph - 45 miles)')
#	)
#
#	speed = models.CharField(
#       		max_length=3,
# 	     		choices=SPEED_TYPE_CHOICES,
#        		default=LESIURE,
#	)
#
#	signed_up = models.DateField("date signed up", auto_now_add=True)
##	email_url = models.UUIDField("random uuid for email confirmation", default=uuid.uuid4, editable=False)
#
#	def __str__(self):
#		return smart_text(self.name)
#
#	
#	def short_speed_display(self):
#		d = dict(self.SPEED_TYPE_CHOICES)
#		x = d[self.speed].split(' ', 1)[0]
#		return x
#		
#
# Velo Feedback
#class VeloFeedback(models.Model):
#	DOM = "dm"
#	SWP_DRV = "sd"
#	SWP_NAV = "sn"
#	FEED_ST = "fs"
#	
#	VOLUNTEER_TYPE = (
#		(DOM, "Domestique (on the bike)"),
#		(SWP_DRV, "Sweep driver"),
#		(SWP_NAV, "Sweep navigator"),
#		(FEED_ST, "Feed station helper"),
#	)
#
#	name = models.CharField('name', help_text="(you can leave this blank)", max_length=200, blank=True) 
#	email =  models.EmailField('email address', help_text="(you can leave this blank)", max_length=200, blank=True)	
#
#	volunteer_type = models.CharField("What was your volunteering role?",
#       		max_length=2,
#        		choices=VOLUNTEER_TYPE,
#        		default=DOM,
#    	)
#
#	question_one = models.TextField('Three things that went well?', help_text="Tell us three things that you thought went particularly well from your experience volunteering at the Velo", blank=True)
#	question_two = models.TextField('Three things we could improve?', help_text="Tell us a few things that we could have improved to make your volunteering experience even better", blank=True)
#
#	support_again = models.BooleanField("Should the Bullets support the Velo in 2018?", help_text="If the opportunity arises, do you think that the Boldmere Bullets should volunteer to support the Velo in 2018?")
#	volunteer_again = models.BooleanField("Would you volunteer to help again?", help_text="If we are involved in the Velo 2018, would you be willing to assist again in some role?")
#	
#	question_three = models.TextField("What information or advice would have been useful?", blank=True)
#	question_four = models.TextField("Final thoughts?", blank=True)
#
#
#
#
## Velo Feedback
#class BulletsRunFeedback(models.Model):
#	name = models.CharField('name', help_text="(you can leave this blank)", max_length=200, blank=True) 
#	email =  models.EmailField('email address', help_text="(you can leave this blank)", max_length=200, blank=True)	
#
#	question_one = models.TextField('Three things that went well?', help_text="Tell us three things that you thought went particularly well from your experience at the Bullets Run", blank=True)
#	question_two = models.TextField('Three things we could improve?', help_text="Tell us a few things that we could have improved to make your Bullets Run experience even better", blank=True)
#
#	run_again = models.BooleanField("Should the Bullets have another charity run in 2018?") 
#
#	question_three = models.TextField("Final thoughts?", blank=True)
#
#	
#
#
#
# for the Velo
#@python_2_unicode_compatible
#class VeloVolunteer(models.Model):
#	RIDER = "r"
#	NON_RIDER = "n"
#	VOLUNTEER_TYPE_CHOICES = (
#		(RIDER, "rider"),
#		(NON_RIDER, "non-rider")
#	)
#
#	bullet = models.ForeignKey(OldBullet, blank=True, null=True)		# RIDERS
#	email =  models.EmailField('email address', max_length=200, blank=True)	# NON RIDER
#	name = models.CharField('name', help_text="Your name", max_length=200, blank=True) # NON RIDER		
#	address = models.TextField("address", help_text="Your address")
#	volunteer_type = models.CharField(
#       		max_length=1,
#        		choices=VOLUNTEER_TYPE_CHOICES,
#       		default=RIDER,
#    	)
#
#Rider fields
#	entered_velo = models.BooleanField("have you entered the Velo?")
#	average_speed = models.CharField('expected average speed for 100mile ride (mph)', max_length=10, blank=True)
#
#	MALE = 'm'
#	FEMALE = 'f'
#	KIT_SEX_CHOICES = (
#		(MALE, 'male-fit'),
#		(FEMALE, 'female-fit')
#	)
#
#	kit_sex = models.CharField('do you want male or female-fit kit?', max_length=1, choices=KIT_SEX_CHOICES, default=MALE) 
#	
#	SIZE_XS = 'xs'
#	SIZE_S = 's'
#	SIZE_M = 'm'
#	SIZE_L = 'l'
#	SIZE_XL = 'xl'
#	SIZE_XXL = 'xxl'
#	SIZE_XXXL = 'xxxl'
#
#	KIT_SIZE_CHOICES = (
#		(SIZE_XS, 'X Small'),
#		(SIZE_S, 'Small'),
#		(SIZE_M, 'Medium'),
#		(SIZE_L, 'Large'),
#		(SIZE_XL, 'X Large'),
#		(SIZE_XXL, 'XX Large'),
#		(SIZE_XXXL, 'XXX Large')
#	)
#	
#	jersey_size = models.CharField('jersey size', max_length=4, choices=KIT_SIZE_CHOICES)
#	short_size =  models.CharField('bib short size', max_length=4, choices=KIT_SIZE_CHOICES)
#
#NonRider fields 
#	tshirt_size =  models.CharField('t-shirt size', max_length=4, choices=KIT_SIZE_CHOICES)
#	drive_van = models.BooleanField("are you willing to drive a van?")
#	drive_bus = models.BooleanField("are you willing to drive a minibus?")
#	contact_no = models.CharField('contact number', max_length=100)
#
#	unique_ref = models.UUIDField("random uuid for emails", default=uuid.uuid4, editable=False)
#
#	feedback_received = models.BooleanField("recieved feedback", default=False)
#
#	def __str__(self):
#		return self.get_name()
#
#	def get_name(self):
#		if (self.bullet != None):
#			return smart_text(self.bullet.name)
#		else:
#			return smart_text(self.name)
#
#	def get_email(self):
#		if (self.bullet != None):
#			return self.bullet.email
#		else:
#			return self.email
#
#
#
#from saleor.order.models import Order
#### import emailit.api
#
#
## for the BulletsRun
#@python_2_unicode_compatible
#class BulletsRunner(models.Model):
#	name = models.CharField("name", max_length=200)
#	address = models.TextField("address")
#	email = models.EmailField('email address', max_length=200)
#	contact_no = models.CharField('contact number', max_length=100)
#	emergency_contact_no = models.CharField('emergency contact number', max_length=100)
#	age = models.PositiveSmallIntegerField('age', help_text="Your age on the 17th September")	
#	club = models.CharField("Club", max_length=200, blank=True)
#	
#	FIVEK = '5'
#	TENK = '10'
#	RACE_LENGTH = (
#		(FIVEK, '5k'),
#		(TENK, '10k')
#	)
#	race = models.CharField('race length', max_length=2, choices=RACE_LENGTH, default=FIVEK)
#
#
#	MALE = 'm'
#	FEMALE = 'f'
#	NOT_GIVEN = '?'
#	RACE_GENDER = (
#		(FEMALE, 'female'),
#		(MALE, 'male'),
#		(NOT_GIVEN, 'not provided')
#	)
#	gender = models.CharField('gender', max_length=1, choices=RACE_GENDER, default=NOT_GIVEN) 
#
#	order_reference = models.ForeignKey(Order, blank=True, null=True)
#	unique_url = models.UUIDField("random GUID for URLs", default=uuid.uuid4, editable=False)
#	paid_offline = models.BooleanField("paid offline", default=False)
#
#	had_email = models.BooleanField("received update email", default=False)
#	had_final_email = models.BooleanField("received final email", default=False)
#
#
#	runner_number = models.PositiveSmallIntegerField("Runner Number", blank=True, null=True, default=None)
#	chip_time = models.CharField("Chip Time", max_length=200, blank=True)
#	gun_time = models.CharField("Gun Time", max_length=200, blank=True)
#
#
#	def paid(self):
#		if (self.order_reference != None):
#			return self.order_reference.is_fully_paid()
#		else:
#			return self.paid_offline
#	
#		
#	def __str__(self):
#		return smart_text(self.name)
#
#
#	def send_runner_email(self, dryrun=False):
#		if self.paid():
#			# ok to email them
#			if self.had_email == False: # safety check
#				if dryrun:
#					print("*** Would email " + str(self.name) + "("+str(self.email) + ") ***")
#					return False
#				else:
#					ctx = {'runner':self}
#					##### emailit.api.send_mail(context=ctx, recipients=self.email, template_base='/email/bulletsrun', from_email='lisa@boldmerebullets.com')
#					self.had_email = True
#					self.save()
#
#					print("Sent an email to " + str(self.email) + " about the Bullets Run")
#
#				return True
#			else:
#				print("Not sending an email to " + str(self.name) + "("+str(self.email) + ") - ALREADY RECEIVED")
#		else:
#			print("Not sending an email to " + str(self.name) + "("+str(self.email) + ") - NOT PAID")
#
#		return False
#
#
#	def send_runner_feedback_email(self, dryrun=False):
#		if self.paid():
#			if dryrun:
#				print("*** Would email " + str(self.name) + "("+str(self.email) + ") ***")
#				return False
#			else:	
#				url = 'https://www.boldmerebullets.com/bullets-run-2017/feedback/' + str(self.unique_url)
#				ctx = {'runner':self, 'feedback_url':url}
#				##### emailit.api.send_mail(context=ctx, recipients=self.email, template_base='/email/bulletsrun_feedback', from_email='lisa@boldmerebullets.com')
#			
#				print("Sent an email to " + str(self.email) + " about feedback on the Bullets Run")
#
#				return True
#		else:
#			print("Not sending an email to " + str(self.name) + "("+str(self.email) + ") - NOT PAID")
#
#		return False
#
#
#
#	def send_runner_final_email(self, dryrun=False):
#		if self.runner_number != None:
#			x = BulletRunnerPhoto.objects.filter(runner_number = self.runner_number).exists()
#			if x: # there are some pictures
#				if self.had_final_email == False: # safety check
#					if dryrun:
#						print("*** Would email " + str(self.name) + "("+str(self.email) + ") ***")
#						return False
#					else:
#						url = 'https://www.boldmerebullets.com/bullets-run-2017/my-photos/' + str(self.unique_url)
#						print("URL = " + str(url))
#						ctx = {'runner':self, 'photo_url':url}
#						###### emailit.api.send_mail(context=ctx, recipients=self.email, template_base='/email/bulletsrun_final', from_email='leaders@boldmerebullets.com')
#						self.had_final_email = True
#						self.save()
#
#						print("Sent a final email to " + str(self.email) + " about the Bullets Run")
#
#						return True
#				else:
#					print("Not sending a final email to " + str(self.name) + "("+str(self.email) + ") - ALREADY RECEIVED")
#			else:
#				print("This runner " + str(self.name) + " doesn't appear in any pictures")
#		else:
#			print("Not sending an email to " + str(self.name) + " - no runner number")
#
#		return False
#
#
#
#
#class BulletRunnerPhoto(models.Model):
#	url = models.URLField("Photo URL")
#	runner_number = models.PositiveSmallIntegerField("Runner Number", null=True, blank=True)
#	
#	def __str__(self):	
#		return "Runner Photo for #" + str(self.runner_number)	
#
#	def get_next(self):
#		"""
#		Get the next object by primary key order
#		"""
#		next = self.__class__.objects.filter(pk__gt=self.pk)
#		try:
#			return next[0]
#		except IndexError:
#			return False
#
#	def get_prev(self):
#		"""
#		Get the previous object by primary key order
#		"""
#		prev = self.__class__.objects.filter(pk__lt=self.pk).order_by('-pk')
#		try:
#			return prev[0]
#		except IndexError:
#			return False
#
#
#class TdBStage(models.Model):
#	name = models.CharField("Stage name", max_length=200)
#	stage_type = models.CharField("Stage type", max_length=200, blank=True, null=True)
#	description = models.TextField("description", blank=True, null=True)
#	valid_from = models.DateField("Valid from")
#	valid_until = models.DateField("Valid until")
#
#	long_route = models.PositiveIntegerField("Long route ID", blank=True, null=True)
#	medium_route = models.PositiveIntegerField("Medium route ID", blank=True, null=True)
#	short_route = models.PositiveIntegerField("Short route ID", blank=True, null=True)
#	social_route = models.PositiveIntegerField("Social route ID", blank=True, null=True)
#
#	long_distance = models.PositiveIntegerField("Long distance", blank=True, null=True)
#	medium_distance = models.PositiveIntegerField("Medium distance", blank=True, null=True)
#	short_distance = models.PositiveIntegerField("Short distance", blank=True, null=True)
#	social_distance = models.PositiveIntegerField("Social distance", blank=True, null=True)
#
#
#	hilly_segment = models.PositiveIntegerField("Hilly segment ID", blank=True, null=True)
#	flat_segment = models.PositiveIntegerField("Flat segment ID", blank=True, null=True)
#	overall_segment = models.PositiveIntegerField("Overall segment ID", blank=True, null=True)
#
#	ss_hilly_segment = models.PositiveIntegerField("Super Social hilly segment ID", blank=True, null=True)
#	ss_flat_segment = models.PositiveIntegerField("Super Social flat segment ID", blank=True, null=True)
#	
#	def __str__(self):
#		return smart_text(self.name)
#
#	def show_details(self):
#		now = timezone.now().date()
#		if (self.valid_from <= now) and (now <= self.valid_until):
#			return True
#		else:
#			return False
#
#
#	def one_route_only(self):
#		return ((self.long_route != None) and ((self.medium_route == None) and (self.short_route == None) and (self.social_route == None)))
#		# we use the long route ID in that situation
#
#
#	def athlete_times(self, athlete_id):
#		hs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.hilly_segment, athlete_id=athlete_id)
#		fs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.flat_segment, athlete_id=athlete_id)
#
#		ss_hs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_hilly_segment, athlete_id=athlete_id)
#		ss_fs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_flat_segment, athlete_id=athlete_id)
#
#		os = TdBLeaderBoard_Entry.objects.filter(segment_id=self.overall_segment, athlete_id=athlete_id)
#
#		return {'hilly_segment': hs, 'flat_segment': fs, 'ss_hilly_segment':ss_hs, 'ss_flat_segment':ss_fs, 'overall':os}
#
#
#	def athlete_done_stage(self, athlete_id):
#		hs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.hilly_segment, athlete_id=athlete_id).exists()
#		fs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.flat_segment, athlete_id=athlete_id).exists()
#
#		ss_hs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_hilly_segment, athlete_id=athlete_id).exists()
#		ss_fs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_flat_segment, athlete_id=athlete_id).exists()
#
#		os = TdBLeaderBoard_Entry.objects.filter(segment_id=self.overall_segment, athlete_id=athlete_id).exists()
#
#		return ((hs and fs) or (ss_hs and ss_fs) or (os))		# got to have done both hilly+flat or the overall segment
#
#
#	def hilly_leaderboard(self):
#		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.hilly_segment)
#
#	def flat_leaderboard(self):
#		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.flat_segment)
#
#
#
#	def hilly_new_leaderboard(self):
#		return NewTDBLeaderBoard.objects.filter(segment_id=self.hilly_segment)
#
#	def flat_new_leaderboard(self):
#		return NewTDBLeaderBoard.objects.filter(segment_id=self.flat_segment)
#
#
#
#	def ss_hilly_leaderboard(self):
#		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_hilly_segment)
#
#	def ss_flat_leaderboard(self):
#		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_flat_segment)
#
#
#	def overall_leaderboard(self):
#		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.overall_segment)
#
#	
#	def completed_leaderboard(self):
##		completed = self.long_leaderboard() | self.medium_leaderboard() | self.short_leaderboard() | self.social_leaderboard()
#		completed = self.hilly_leaderboard() | self.flat_leaderboard() | self.overall_leaderboard() | self.ss_hilly_leaderboard() | self.ss_flat_leaderboard()
#		x = completed.order_by('athlete_name').distinct('athlete_name')			
#		return x
#
#	def how_many_completed(self):
#		x = self.completed_leaderboard()
#		return x.count()
#
#	class Meta:
#		verbose_name = "TdB Stage"
#		verbose_name_plural = "TdB Stages"
#
#
#class TdBLeaderBoard_Entry(models.Model):
#	segment_id = models.PositiveIntegerField("Segment ID")
#	athlete_id = models.PositiveIntegerField("Athlete ID")
#	activity_id = models.PositiveIntegerField("Activity ID")
#	athlete_name = models.CharField("Athlete Name", max_length=300)
#	time_taken = models.DurationField("Time Taken")
#	date_completed = models.DateField("Date completed")
#
#	def __str__(self):
#		return "Leaderboard for " + str(self.athlete_name) + " - " + str(self.segment_id) + " at " + str(self.date_completed)
#
#	class Meta:
#		verbose_name = "TdB Leaderboard Entry"
#		verbose_name_plural = "TdB Leaderboard Entries"
#
#
#class NewTDBLeaderBoard(models.Model):
#	segment_id = models.PositiveIntegerField("Segment ID")
#	athlete_id = models.PositiveIntegerField("Athlete ID")
#	activity_id = models.PositiveIntegerField("Activity ID")
#	athlete_name = models.CharField("Athlete Name", max_length=300)
#	time_taken = models.DurationField("Time Taken")
#	date_completed = models.DateField("Date completed")
#
#	def __str__(self):
#		return "NEW Leaderboard for " + str(self.athlete_name) + " - " + str(self.segment_id) + " at " + str(self.date_completed)
#
#	class Meta:
#		verbose_name = "NEW TdB Leaderboard Entry"
#		verbose_name_plural = "NEW TdB Leaderboard Entries"
#
#	HILL = 'h'
#	FLAT = 'f'
#	OTHER = '?'
#	PROLOGUE = 'p'
#	STAGE_TYPE = (
#		(HILL, 'hilly'),
#		(FLAT, 'flat'),
#		(OTHER, 'other'),
#		(PROLOGUE, 'prologue')
#	)
#	stage_type = models.CharField('Stage Type', max_length=1, choices=STAGE_TYPE, default=PROLOGUE) 
#
#
#
#
### CTS Mobile App stuff
#
#class CTSVehicle(models.Model):
#	number = models.PositiveIntegerField("Vehicle Number")
#	name = models.CharField("Vehicle Name", max_length=300)
#	
#	def __str__(self):
#		return "CTS Vehicle " + str(self.number)
#
#	def get_latest_position(self):
#		return self.ctsvehicleposition_set.latest()
#
#	class Meta:
#		ordering = ['number']
#
#
#class CTSRider(models.Model):
#	name = models.CharField("Athlete Name", max_length=300)
#
#	def get_latest_position(self):			
#		#x = self.ctsriderposition_set.all().order_by("-id")[:2]
#		#return reversed(x)
#		return self.ctsriderposition_set.latest()
#
#	def __str__(self):
#		return "CTS Rider " + str(self.name)
#
#
#class CTSRiderPosition(models.Model):
#	rider = models.ForeignKey(CTSRider)
#	distance_from_start = models.DecimalField("Distance from start", max_digits=9, decimal_places=6)
#	timestamp = models.DateTimeField('Timestamp')
#	lat = models.DecimalField("Latitude", max_digits=9, decimal_places=6)
#	lon = models.DecimalField("Longitude", max_digits=9, decimal_places=6)
#
#	def __str__(self):
#		return "CTS Rider position for " + str(self.rider)	
#
#	class Meta:
#		get_latest_by = 'timestamp'
#
#	
#class CTSVehiclePosition(models.Model):
#	vehicle = models.ForeignKey(CTSVehicle)
#	timestamp = models.DateTimeField('Time Stamp')
#	lat = models.DecimalField("Latitude", max_digits=9, decimal_places=6)
#	lon = models.DecimalField("Longitude", max_digits=9, decimal_places=6)
#	
#	def __str__(self):
#		return "CTS Vehicle Position for " + str(self.vehicle)
#
#	class Meta:
#		get_latest_by = 'timestamp'
#
