philoApp.controller('exportResults', ['$scope', '$location', function($scope, $location) {
    $scope.exportResults = function() {
        var exportLink = window.location.href + "&format=json";
        window.open(exportLink);
    }
}])