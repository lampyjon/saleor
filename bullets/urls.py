from django.conf.urls import include, url, handler404
from . import views
from django.views.generic import TemplateView, RedirectView
from django.shortcuts import redirect

from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^register/$', views.register, name='register'),
    url(r'^register/success/$', TemplateView.as_view(template_name="bullets/registered.html"), name='registered'),
    url(r'^register/about/$', TemplateView.as_view(template_name="bullets/about-registration.html"), name='about-registration'),
    url(r'^register/remove/$', views.unregister, name='unregister'),
    url(r'^register/removed/$', TemplateView.as_view(template_name="bullets/unregistered.html"), name='unregistered'),

    url(r'^register/confirm-email/(?P<uuid>[0-9a-z-]+)/$', views.confirm_email, name='confirm-bullet-email'),
    url(r'^register/confirm-remove/(?P<uuid>[0-9a-z-]+)/$', views.confirm_remove, name='unregister-bullet-email'),

    url(r'^rides/info/$', TemplateView.as_view(template_name="bullets/ride_info.html"), name='ride-info'),
    url(r'^rides/routes/$', TemplateView.as_view(template_name="bullets/ride_routes.html"), name='ride-routes'),
    url(r'^runs/info/$', TemplateView.as_view(template_name="bullets/run_info.html"), name='run-info'),
    url(r'^runs/routes/$', TemplateView.as_view(template_name="bullets/run_routes.html"), name='run-routes'),
    url(r'^runs/sunday/$', TemplateView.as_view(template_name="bullets/run_sunday.html"), name='run-sunday'),
    url(r'^runs/tuesday/$', TemplateView.as_view(template_name="bullets/run_tuesday.html"), name='run-tuesday'),

    url(r'^collective-code/$', TemplateView.as_view(template_name="bullets/collective-code.html"), name='collective-code'),
    url(r'^history/$', TemplateView.as_view(template_name="bullets/history.html"), name='history'),
    url(r'^core-team/$', TemplateView.as_view(template_name="bullets/about.html"), name='core'),
    url(r'^contact-us/$', views.contact, name='contact'),
    url(r'^events/$', TemplateView.as_view(template_name="bullets/events.html"), name='events'),
    url(r'^support/affliates$', TemplateView.as_view(template_name="bullets/affliates.html"), name='affliates'),

    url(r'^news/latest/$', views.NewsListView.as_view(), name='news'),
    url(r'^news/item/(?P<slug>[-\w]+)/$', views.news_item, name='news-item'),
#    url(r'^news/latest/$', TemplateView.as_view(template_name="bullets/news.html"), name='news'),

    url(r'^info/delivery-times/$', TemplateView.as_view(template_name="bullets/delivery-times.html"), name='delivery-times'),


    url(r'^core-team-admin/$', views.bullets_core_team, name='core-team-admin'), 

# Spring Classic Riders
#    url(r'^special-events/spring-classics/$', TemplateView.as_view(template_name="bullets/spring-classics/spring-classics.html"), name='spring-classics'),
#    url(r'^special-events/spring-classics/milan-san-remo/$', TemplateView.as_view(template_name="bullets/spring-classics/spring-classics-milan.html"), name='spring-milan'),
#    url(r'^special-events/spring-classics/the-hell-of-the-north/$', TemplateView.as_view(template_name="bullets/spring-classics/spring-classics-paris.html"), name='spring-paris'),
  

# Bullets Run URLs
   url(r'^bullets-run-2017/$', TemplateView.as_view(template_name="bullets/bullets_run.html"), name='bullets-run'),
#   url(r'^bullets-run-2017/register$', views.bullets_run_register, name='bullets-run-register'),
#
#   url(r'^bullets-run-2017/reminder/(?P<uuid>[0-9a-z-]+)/$', views.bullets_run_reminder, name='bullets-run-reminder'),	# used in reminder emails!
#
#   url(r'^bullets-run-2017/stats$', views.bullets_run_stats, name='bullets-run-stats'),
#   url(r'^bullets-run-2017/offline$', views.bullets_run_offline, name='bullets-run-offline'),		# For Lisa to add offline payments
#   url(r'^bullets-run-2017/admin$', views.bullets_run_admin, name='bullets-run-admin'),			# For Lisa to view runner details
#   url(r'^bullets-run-2017/admin/edit/(?P<pk>\d+)$', views.bullets_run_admin_edit, name='bullets-run-admin-edit'),	# For Lisa to edit runner details
#   url(r'^bullets-run-2017/admin/delete/(?P<pk>\d+)$', views.bullets_run_admin_delete, name='bullets-run-admin-delete'),	# For Lisa to delete runner details



# Velo URLs  
#    url(r'^special-events/velo/$', views.velo, name='velo'),
#    url(r'^special-events/velo/rider/$', views.velo_rider, name='velo-rider'),
#    url(r'^special-events/velo/non-rider/$', views.velo_nonrider, name='velo-nonrider'),
#    url(r'^special-events/velo/view/(?P<uuid>[0-9a-z-]+)/$', views.velo_details, name='velo-details'),
##    url(r'^special-events/velo/view/(?P<uuid>[0-9a-z-]+)/family-members/$', views.velo_details, name='velo-family-details'),
#    url(r'^special-events/velo/delete/$', views.velo_delete, name='velo-delete'),
#    url(r'^special-events/velo/stats/$', views.velo_stats, name='velo-stats'),
#    url(r'^velo/$', RedirectView.as_view(pattern_name='velo', permanent=True)),


#    url(r'^special-events/velo/admin/$', views.velo_admin, name='velo-admin'),		## for Kate to view the volunteers
#    url(r'^special-events/velo/admin/delete/(?P<pk>\d+)$', views.velo_admin_delete, name='velo-admin-delete'),	# For Kate to delete velo details
#    url(r'^special-events/velo/admin/email/$', views.velo_admin_email, name='velo-admin-email'),	## For Jon to email the non-riders - temp link


# Tour De Boldmere 2017 URLs
    url(r'^Tour-de-Boldmere-2017/$', views.tdb, name='tdb2017'),
    url(r'^Tour-de-Boldmere-2017/stage/(?P<pk>\d+)/$', views.tdbStage, name='tdb2017-stage'),
    url(r'^Tour-de-Boldmere-2017/leaderboards/$', views.tdbLeaderBoard, name='tdb2017-leaderboard'),





# Chase The Sun
    url(r'^special-events/chase-the-sun/$', TemplateView.as_view(template_name="bullets/cts.html"), name='cts'),



#    url(r'^cts-mobile/$', views.cts_mobile, name='cts-mobile'),
#    url(r'^cts-mobile/menu/$', views.cts_mobile_menu, name='cts-mobile-menu'),
#    url(r'^cts-mobile/map/$', views.cts_mobile_map, name='cts-mobile-map'),
#    url(r'^cts-mobile/map/(?P<pk>\d+)/$', views.cts_mobile_map, name='cts-mobile-map-car'),

#    url(r'^cts-mobile/vehicle_list/$', views.cts_mobile_vehicle_list, name='cts-mobile-vehicle-list'),
#    url(r'^cts-mobile/support-stop/$', views.cts_mobile_support_stop, name='cts-mobile-support-stop'),
#    url(r'^cts-mobile/rider-positions/$', views.cts_mobile_rider_positions, name='cts-mobile-rider-positions'),
#    url(r'^cts-mobile/logout/$', views.cts_mobile_logout, name='cts-mobile-logout'),


#    url(r'^cts-mobile/ajax/vehicle_position/$', views.cts_vehicle_position_ajax, name='cts-vehicle-position-ajax'),
#    url(r'^cts-mobile/ajax/route/$', TemplateView.as_view(template_name="bullets/cts/CTS.gpx"), name='cts-route-ajax'),
#    url(r'^cts-mobile/ajax/rider_position/$', views.cts_rider_position_ajax, name='cts-rider-position-ajax'),
#    url(r'^cts-mobile/ajax/rider_position/checkin/$', views.cts_rider_checkin_ajax, name='cts-rider-checkin-ajax'),


#    url(r'^cts/$', views.cts_big_map, name='cts-big-map'),




    ## REDIRECT for leaders app
    url(r'^leaders/$', views.leaders, name='leaders'),


   #### SPECIAL URLS
#    url(r'^.well-known/acme-challenge/(?P<part1>[a-zA-Z0-9_.-]+)$', views.CertBot, name='certbot'),	# For CertBot
    url(r'^google03f79ced8f1af3fd.html$', TemplateView.as_view(template_name="google.html"), name='google'),   # For google
    url(r'^robots.txt$',  TemplateView.as_view(template_name="robots.txt"), name="robots-txt"),		# for robots
    url(r'BingSiteAuth.xml$', TemplateView.as_view(template_name="BingSiteAuth.xml"), name="bing"),


    ### LEGACY URLS
 
    url(r'^who-are-the-bullets-2/$', RedirectView.as_view(pattern_name='index', permanent=True)),
    url(r'^who-are-the-bullets-2/cycling-collective/cycling-routes/$', RedirectView.as_view(pattern_name='ride-routes', permanent=True)),
    url(r'^running/$', RedirectView.as_view(pattern_name='run-info', permanent=True)),
    url(r'^events_all/', RedirectView.as_view(pattern_name='events', permanent=True)),
    url(r'^event/', RedirectView.as_view(pattern_name='events', permanent=True)),
    url(r'^who-are-the-bullets-2/running-collective/', RedirectView.as_view(pattern_name='run-info', permanent=True)),
    url(r'^who-are-the-bullets-2/cycling-collective/', RedirectView.as_view(pattern_name='ride-info', permanent=True)),
    url(r'^who-are-the-bullets-2/', RedirectView.as_view(pattern_name='history', permanent=True)),



    # Summernote
    url(r'^magic_editor/', include('django_summernote.urls')), 


    # Other apps
    url(r'^bullets-shop/', include('saleor.urls')),
    url(r'^vlb-admin/', admin.site.urls),
]


handler404 = 'bullets.views.error404'


