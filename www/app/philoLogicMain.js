var philoApp = angular.module('philoApp', ['ngRoute', 'ngTouch', 'ngSanitize', 'ngCookies', 'angular-velocity', 'ui.utils', 'infinite-scroll']);

philoApp.controller('philoMain', ['$rootScope', '$scope', '$location', 'accessControl', 'textNavigationValues', 'request',
                                  function($rootScope, $scope, $location, accessControl, textNavigationValues, request) {
    
    $rootScope.philoConfig = philoConfig;
    
    // Check access control
    if (!$rootScope.philoConfig.access_control) {
        $rootScope.authorized = true;
    } else {
        $rootScope.accessRequest = request.script({
            script: 'access_request.py'
        });
    }
        
    $rootScope.report = $location.search().report || philoReport;
    $rootScope.formData = {
        report: $rootScope.report,
        method: "proxy"
        };
    
    $scope.$on('$locationChangeStart', function(e) {
        var paths = $location.path().split('/').filter(Boolean);
        if (paths[0] == "query") {
            $rootScope.report = $location.search().report;
        } else if (paths[0] == "navigate") {
            if (paths[paths.length-1] === "table-of-contents") {
                $rootScope.report = "table-of-contents";
            } else {
                $rootScope.report = 'textNavigation';
            }
        } else {
            $rootScope.report = "landing_page";
        } 
        if ($rootScope.report !== 'textNavigation') {
            textNavigationValues.citation = {};
            textNavigationValues.tocElements = false;
            textNavigationValues.tocOpen = false;
            textNavigationValues.navBar = false;
        }
    });
}]);

philoApp.config(['$routeProvider', '$locationProvider',
  function($routeProvider, $locationProvider) {
    $routeProvider.
        when('/', {
            templateUrl: function(array) {
                return 'app/components/landingPage/landing_page.html';
            },
            controller: 'landingPage',
            controllerAs: 'lp'
        }).
        when('/query?:queryArgs', {
            templateUrl: function(queryArgs) {
                var report = queryArgs.report;
                if (report === "concordance" || report === "kwic" || report === "bibliography" || report === "concordance_from_collocation" || report === "word_property_filter") {
                    var template = 'app/components/concordanceKwic/concordanceKwic.html';
                } else if (report === "collocation") {
                    var template = 'app/components/collocation/collocation.html';
                } else if (report === "time_series") {
                    var template = 'app/components/timeSeries/timeSeries.html';
                } else {
                    var template = 'app/components/landingPage/landing_page.html'; 
                }
                return template;
            }
        }).
        when('/navigate/:pathInfo*\/', {
            templateUrl: function(queryArgs) {
                var pathInfo = queryArgs.pathInfo.split('/');
                if (pathInfo[pathInfo.length - 1] == "table-of-contents") {
                    return 'app/components/tableOfContents/tableOfContents.html';
                } else {
                    return 'app/components/textNavigation/textNavigation.html';
                }
            }
        }).
        when('/access-control', {
            templateUrl: 'app/components/accessControl/accessControl.html'
        }).
        otherwise({
          redirectTo: '/'
        });
    $locationProvider.html5Mode({
        enabled: true
    });
}]);