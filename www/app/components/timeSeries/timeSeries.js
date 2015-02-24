"use strict";

philoApp.controller('timeSeriesCtrl', ['$scope', '$rootScope', '$location', 'radio', 'URL', function($scope, $rootScope, $location, radio, URL) {
    $rootScope.formData = angular.copy($location.search());
    if ($rootScope.formData.q === "" && $rootScope.report !== "bibliography") {
        $rootScope.formData.report = "bibliography";
        $location.url(URL.objectToString($rootScope.formData, true));
    }
    $rootScope.report = "time_series";
    
    $scope.percent = 0;
    $scope.interval = parseInt($rootScope.formData.year_interval);
    
    $scope.frequencyType = 'absolute_time';
    $scope.toggleFrequency = function(frequencyType) {
        $('#time-series-buttons button').removeClass('active');
        $('#' + frequencyType).addClass('active');
        console.log(frequencyType)
        $scope.frequencyType = frequencyType;
    }
    
}]);