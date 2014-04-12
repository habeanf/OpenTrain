""" comment 
export DJANGO_SETTINGS_MODULE="opentrain.settings"
"""
import os
os.environ['DJANGO_SETTINGS_MODULE']='opentrain.settings'
#/home/oferb/docs/train_project/OpenTrains/webserver
import gtfs.models
import analysis.models
import numpy as np
from scipy import spatial
try:
    import matplotlib.pyplot as plt
except ImportError:
    pass
import simplekml
import config
import itertools
import datetime
from unittest import TestCase
import unittest
import time
from display_utils import *
from export_utils import *
import shapes
from train_tracker import add_report, print_possible_trips, get_trips

import stops
from common.mock_reports_generator import generate_mock_reports
from analysis.models import SingleWifiReport
from redis_intf.client import get_redis_pipeline, get_redis_client

class train_tracker_test(TestCase):

    def track_device(self, device_id, do_print=False, do_preload_reports=True, set_reports_to_same_weekday_last_week=True):
        #device_coords, device_timestamps, device_accuracies_in_meters, device_accuracies_in_coords = get_location_info_from_device_id(device_id)
        now = ot_utils.get_localtime_now()
        reports_queryset = self.get_device_id_reports(device_id)
        tracker_id = device_id
        
        fps_period_start = time.clock()
        fps_period_length = 100
        if do_preload_reports:
            reports_queryset = list(reports_queryset)
        count = len(reports_queryset) if isinstance(reports_queryset, list) else reports_queryset.count()
        for i in xrange(count):
            if i % fps_period_length == 0:
                elapsed = (time.clock() - fps_period_start)
                if elapsed > 0:
                    print('%d\t%.1f qps' % (i, fps_period_length/elapsed))
                else:
                    print('Elapsed time should be positive but is %d' % (elapsed))
                fps_period_start = time.clock()                
            
            if i % 900 == 0:
                trips = get_trips(tracker_id)
            report = reports_queryset[i]
            
            if set_reports_to_same_weekday_last_week:
                # fix finding same weekday last week by http://stackoverflow.com/questions/6172782/find-the-friday-of-previous-last-week-in-python
                day_fix = (now.weekday() - report.timestamp.weekday()) % 7
                day = now + datetime.timedelta(days=-day_fix)
                # move day and correct for DST (daylight savings time)
                dst_before = report.get_timestamp_israel_time().dst()
                report.timestamp = report.timestamp.replace(year=day.year, month=day.month, day=day.day)
                dst_after = report.get_timestamp_israel_time().dst()
                report.timestamp -= dst_after-dst_before
                
            add_report(report)
            

        #tracker.print_tracked_stop_times()
        #tracker.print_possible_trips()
        trips, deviation_in_seconds = get_trips(tracker_id)
        return tracker_id, trips
        
  
    def track_mock_reports(self, reports, tracker_id):
        for i, report in enumerate(reports):
            add_report(report)
        
        trips, deviation_in_seconds = get_trips(tracker_id)
        return tracker_id, trips
    
    def teXXXst_tracker_on_mock_device_multiple_trips(self, device_id = 'fake_device_1', trip_ids = ['010314_07117','010314_07117'], remove_some_locations=True):
        self.test_tracker_on_mock_device(device_id, trip_ids, remove_some_locations)
        
    def test_tracker_on_mock_device(self, device_id = 'fake_device_1', trip_ids = ['010314_07117'], remove_some_locations=True):
        if not isinstance(trip_ids, list):
            trip_ids = [trip_ids]
        tracker_id = device_id
        self.remove_from_redis(tracker_id)
        reports = []
        for trip_id in trip_ids:
            day = datetime.datetime.strptime(trip_id.split('_')[0], '%d%m%y')
            now = ot_utils.get_localtime_now() # we want to get the correct timezone so we take it from get_localtime_now()
            day = now.replace(year=day.year, month=day.month, day=day.day)
            trip_reports = generate_mock_reports(device_id=device_id, trip_id=trip_id, nostop_percent=0.05, day=day)
            reports += trip_reports

        for report in reports[::2]:
            del report.my_loc_mock
        
        tracker_id, trips = self.track_mock_reports(reports, tracker_id)
        print_possible_trips(tracker_id)
        self.remove_from_redis(tracker_id)
        self.assertEquals(len(trips), 1)
        self.assertTrue(self.is_trip_in_list(trips, trip_id))
        
    def test_tracker_on_real_devices(self):    
        device_ids = []
        trip_suffixes_list = []
        #device_ids.append('1cb87f1e')# Udi's trip  
        #trip_suffixes_list.append(['_00073'])
        #device_ids.append('02090d12')# Eran's trip
        #trip_suffixes_list.append(['_00077', '_00177'])
        device_ids.append('f752c40d')# Ofer's trip
        trip_suffixes_list.append(['_00283'])

        self.remove_from_redis(device_ids)
        
        for i in xrange(len(device_ids)):
            device_id = device_ids[i] 
            trip_suffixes = trip_suffixes_list[i]
            tracker_id, trips = self.track_device(device_id, do_preload_reports=True)
            print trips
            self.assertEquals(len(trips), len(trip_suffixes))
            for trip_suffix in trip_suffixes:
                self.assertTrue(self.is_trip_in_list(trips, trip_suffix))
      
        self.remove_from_redis(device_ids)
        
    def remove_from_redis(self, device_ids):
        if isinstance(device_ids, basestring):
            device_ids = [device_ids]
        cl = get_redis_client()
        keys = []
        for device_id in device_ids:
            keys.extend(cl.keys(pattern='train_tracker:%s*' % (device_id)))
        if len(keys) > 0:
            cl.delete(*keys)
            

    def is_trip_in_list(self, trips, trip_id_end):
        return len([x for x in trips if x.endswith(trip_id_end)]) > 0

    def get_device_id_reports(self, device_id):
        qs = analysis.models.Report.objects.filter(device_id=device_id)#,my_loc__isnull=False)
        #qs = qs.filter(timestamp__day=device_date_day,timestamp__month=device_date_month,timestamp__year=device_date_year)
        qs = qs.order_by('timestamp')
        qs = qs.prefetch_related('wifi_set','my_loc')
        #reports = list(qs) takes a long time
        return qs    
        
if __name__ == '__main__':
    unittest.main()