from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^trips/trips-for-date/$',views.get_trip_ids_for_date),
    url(r'^trips/current/$',views.get_current_trips),
    url(r'^trips/cur-location/$',views.get_trips_location,name='api-live-trips'),
    url(r'^trips/(?P<trip_id>\w+)/details/$',views.get_trip_details),
    url(r'^devices/(?P<device_id>\w+)/reports/',views.get_device_reports), 
    url(r'^devices/$',views.get_devices),
    
)



