from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import smart_text, python_2_unicode_compatible
from autoslug import AutoSlugField
from django.urls import reverse


# this model holds values we calcuate sporadically for the site, such as the number of strava runners and cyclists

class SiteValue(models.Model):
	name = models.CharField(max_length=30)
	value = models.TextField()

	def __str__(self):
        	return self.name + " = " + self.value


RUN = 'run'
RIDE = 'ride'

ACTIVITY_TYPE_CHOICES = (
	(RUN, 'Run'),
	(RIDE, 'Ride'),
	)

# This model holds a minimised cache of every strava activity we've seen from the club members
class ActivityCache(models.Model):
	activity_id = models.CharField('Strava ID', max_length=30)
	activity_type = models.CharField('Type',
       		max_length=4,
        	choices=ACTIVITY_TYPE_CHOICES,
        	default=RIDE,
   		)
	distance = models.PositiveIntegerField('Distance')
	start_date = models.DateTimeField('Activity Date')



# this is the registration database
import uuid
@python_2_unicode_compatible
class Bullet(models.Model):
	name = models.CharField("name", max_length=200)
	postcode = models.CharField('first part of postcode', max_length=5)
	email = models.EmailField('email address', max_length=200)
	contact_no = models.CharField('contact number', max_length=100)
	over_18 = models.BooleanField('over 18', help_text='Please confirm that you are over 18?')
	get_emails = models.BooleanField("happy to receive emails", help_text='Can we contact you regarding Collective events?')
	joined = models.DateField("date joined", auto_now_add=True)
	email_checked = models.BooleanField('confirmed email', default=False)
	email_check_ref = models.UUIDField("random uuid for email confirmation", default=uuid.uuid4, editable=False)
        
	# TODO: admin view - how many bullets joined this week / how many left this week

	class Meta:
		ordering = ['name']

	def __str__(self):
		return smart_text(self.name)


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
#	bullet = models.ForeignKey(Bullet, blank=True, null=True)		# RIDERS
#	email =  models.EmailField('email address', max_length=200, blank=True)	# NON RIDER
#	name = models.CharField('name', help_text="Your name", max_length=200, blank=True) # NON RIDER		
#	address = models.TextField("address", help_text="Your address")
#	volunteer_type = models.CharField(
 #       		max_length=1,
#        		choices=VOLUNTEER_TYPE_CHOICES,
#        		default=RIDER,
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
#   	tshirt_size =  models.CharField('t-shirt size', max_length=4, choices=KIT_SIZE_CHOICES)
#	drive_van = models.BooleanField("are you willing to drive a van?")
#	drive_bus = models.BooleanField("are you willing to drive a minibus?")
#	contact_no = models.CharField('contact number', max_length=100)
#
#	unique_ref = models.UUIDField("random uuid for emails", default=uuid.uuid4, editable=False)
#
#	
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


from saleor.order.models import Order


# for the BulletsRun
@python_2_unicode_compatible
class BulletsRunner(models.Model):
	name = models.CharField("name", max_length=200)
	address = models.TextField("address")
	email = models.EmailField('email address', max_length=200)
	contact_no = models.CharField('contact number', max_length=100)
	emergency_contact_no = models.CharField('emergency contact number', max_length=100)
	age = models.PositiveSmallIntegerField('age', help_text="Your age on the 17th September")	
	club = models.CharField("Club", max_length=200, blank=True)
	
	FIVEK = '5'
	TENK = '10'
	RACE_LENGTH = (
		(FIVEK, '5k'),
		(TENK, '10k')
	)
	race = models.CharField('race length', max_length=2, choices=RACE_LENGTH, default=FIVEK)


	MALE = 'm'
	FEMALE = 'f'
	NOT_GIVEN = '?'
	RACE_GENDER = (
		(FEMALE, 'female'),
		(MALE, 'male'),
		(NOT_GIVEN, 'not provided')
	)
	gender = models.CharField('gender', max_length=1, choices=RACE_GENDER, default=NOT_GIVEN) 

	order_reference = models.ForeignKey(Order, blank=True, null=True)
	unique_url = models.UUIDField("random GUID for URLs", default=uuid.uuid4, editable=False)
	paid_offline = models.BooleanField("paid offline", default=False)

	def paid(self):
		if (self.order_reference != None) or (self.paid_offline):		### TODO: possibly should check the order at the end of order_ref to see if it is paid?
			return True
		else:
			return False

	def __str__(self):
		return smart_text(self.name)


class News(models.Model):
	title = models.CharField("title", max_length=100)
	extra_title = models.CharField("extra title text (not in link)", max_length=100, blank=True, null=True)
	slug = AutoSlugField(populate_from='title', editable=False)
	redirect_to = models.URLField("redirection story - where to go?", blank=True, null=True)
	story = models.TextField("story", blank=True, null=True)

	date_added = models.DateField("date added", auto_now_add=True)
	display_after = models.DateField("publish on")
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


from django.utils import timezone


class TdBStage(models.Model):
	name = models.CharField("Stage name", max_length=200)
	stage_type = models.CharField("Stage type", max_length=200, blank=True, null=True)
	description = models.TextField("description", blank=True, null=True)
	valid_from = models.DateField("Valid from")
	valid_until = models.DateField("Valid until")

	long_route = models.PositiveIntegerField("Long route ID", blank=True, null=True)
	medium_route = models.PositiveIntegerField("Medium route ID", blank=True, null=True)
	short_route = models.PositiveIntegerField("Short route ID", blank=True, null=True)
	social_route = models.PositiveIntegerField("Social route ID", blank=True, null=True)

	long_distance = models.PositiveIntegerField("Long distance", blank=True, null=True)
	medium_distance = models.PositiveIntegerField("Medium distance", blank=True, null=True)
	short_distance = models.PositiveIntegerField("Short distance", blank=True, null=True)
	social_distance = models.PositiveIntegerField("Social distance", blank=True, null=True)


	hilly_segment = models.PositiveIntegerField("Hilly segment ID", blank=True, null=True)
	flat_segment = models.PositiveIntegerField("Flat segment ID", blank=True, null=True)
	overall_segment = models.PositiveIntegerField("Overall segment ID", blank=True, null=True)

	ss_hilly_segment = models.PositiveIntegerField("Super Social hilly segment ID", blank=True, null=True)
	ss_flat_segment = models.PositiveIntegerField("Super Social flat segment ID", blank=True, null=True)
	
	def __str__(self):
		return smart_text(self.name)

	def show_details(self):
		now = timezone.now().date()
		if (self.valid_from <= now) and (now <= self.valid_until):
			return True
		else:
			return False


	def one_route_only(self):
		return ((self.long_route != None) and ((self.medium_route == None) and (self.short_route == None) and (self.social_route == None)))
		# we use the long route ID in that situation


	def athlete_done_stage(self, athlete_id):
		hs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.hilly_segment, athlete_id=athlete_id).exists()
		fs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.flat_segment, athlete_id=athlete_id).exists()

		ss_hs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_hilly_segment, athlete_id=athlete_id).exists()
		ss_fs = TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_flat_segment, athlete_id=athlete_id).exists()

		os = TdBLeaderBoard_Entry.objects.filter(segment_id=self.overall_segment, athlete_id=athlete_id).exists()

		return ((hs and fs) or (ss_hs and ss_fs) or (os))		# got to have done both hilly+flat or the overall segment


	def hilly_leaderboard(self):
		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.hilly_segment)

	def flat_leaderboard(self):
		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.flat_segment)


	def ss_hilly_leaderboard(self):
		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_hilly_segment)

	def ss_flat_leaderboard(self):
		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.ss_flat_segment)


	def overall_leaderboard(self):
		return TdBLeaderBoard_Entry.objects.filter(segment_id=self.overall_segment)

	
	def completed_leaderboard(self):
#		completed = self.long_leaderboard() | self.medium_leaderboard() | self.short_leaderboard() | self.social_leaderboard()
		completed = self.hilly_leaderboard() | self.flat_leaderboard() | self.overall_leaderboard() | self.ss_hilly_leaderboard() | self.ss_flat_leaderboard()
		x = completed.order_by('athlete_name').distinct('athlete_name')			
		return x

	def how_many_completed(self):
		x = self.completed_leaderboard()
		return x.count()

	class Meta:
		verbose_name = "TdB Stage"
		verbose_name_plural = "TdB Stages"


class TdBLeaderBoard_Entry(models.Model):
	segment_id = models.PositiveIntegerField("Segment ID")
	athlete_id = models.PositiveIntegerField("Athlete ID")
	activity_id = models.PositiveIntegerField("Activity ID")
	athlete_name = models.CharField("Athlete Name", max_length=300)
	time_taken = models.DurationField("Time Taken")
	date_completed = models.DateField("Date completed")

	def __str__(self):
		return "Leaderboard for " + str(self.athlete_name) + " - " + str(self.segment_id) + " at " + str(self.date_completed)

	class Meta:
		verbose_name = "TdB Leaderboard Entry"
		verbose_name_plural = "TdB Leaderboard Entries"




### CTS Mobile App stuff

class CTSVehicle(models.Model):
	number = models.PositiveIntegerField("Vehicle Number")
	name = models.CharField("Vehicle Name", max_length=300)
	
	def __str__(self):
		return "CTS Vehicle " + str(self.number)

	def get_latest_position(self):
		return self.ctsvehicleposition_set.latest()

	class Meta:
		ordering = ['number']


class CTSRider(models.Model):
	name = models.CharField("Athlete Name", max_length=300)

	def get_latest_position(self):			
		#x = self.ctsriderposition_set.all().order_by("-id")[:2]
		#return reversed(x)
		return self.ctsriderposition_set.latest()

	def __str__(self):
		return "CTS Rider " + str(self.name)


class CTSRiderPosition(models.Model):
	rider = models.ForeignKey(CTSRider)
	distance_from_start = models.DecimalField("Distance from start", max_digits=9, decimal_places=6)
	timestamp = models.DateTimeField('Timestamp')
	lat = models.DecimalField("Latitude", max_digits=9, decimal_places=6)
	lon = models.DecimalField("Longitude", max_digits=9, decimal_places=6)

	def __str__(self):
		return "CTS Rider position for " + str(self.rider)	

	class Meta:
		get_latest_by = 'timestamp'

	
class CTSVehiclePosition(models.Model):
	vehicle = models.ForeignKey(CTSVehicle)
	timestamp = models.DateTimeField('Time Stamp')
	lat = models.DecimalField("Latitude", max_digits=9, decimal_places=6)
	lon = models.DecimalField("Longitude", max_digits=9, decimal_places=6)
	
	def __str__(self):
		return "CTS Vehicle Position for " + str(self.vehicle)

	class Meta:
		get_latest_by = 'timestamp'
