// Generated by CoffeeScript 1.7.1

  (function() {
    var app;
    app = angular.module('app', []);
    Mock.mockjax(app);
    app.controller('appCtrl', function($scope, $http) {
      var box;
      box = $scope.box = [];
      $scope.get = function() {
        $http.get('http://g.cn')
        .success(function(data) {
          return box.push(data);
        });
      };
    });
  })();
