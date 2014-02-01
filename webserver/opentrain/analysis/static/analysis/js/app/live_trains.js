"use strict";
// app.js

var app = angular.module('live_trains', ['my.services', 'my.filters', 'my.directives', 'my.leaflet', 'leaflet-directive']);

app.controller('LiveTrainsController', ['$scope', 'MyHttp', 'MyUtils', 'MyLeaflet', '$timeout', 'leafletData', '$window', '$interval',
function($scope, MyHttp, MyUtils, MyLeaflet, $timeout, leafletData, $window, $interval) {
	$scope.input = {
		showTrips : {},
	};
	$scope.initTrips = function() {
		$scope.tripDatas = {};
		$scope.trips = [];
		MyHttp.get('/api/v1/live-trips/?limit=100').success(function(data) {
			$scope.trips = data.objects;
			$scope.trips.forEach(function(trip) {
				$scope.loadTripData(trip.trip_id);
			});
		});
	};
	$scope.loadTripData = function(trip_id) {
		$scope.input.showTrips[trip_id] = true;
		MyHttp.get('/api/v1/trips/' + trip_id + '/').success(function(data) {
			console.log(data);
			console.log('loaded data for trip ' + trip_id);
			$scope.tripDatas[trip_id] = data;
		});
	};
	$scope.initTrips();
}]);
