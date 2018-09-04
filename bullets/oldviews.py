### Legacy Views - may need again in the future





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

