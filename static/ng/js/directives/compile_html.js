angular.module('app', []);
angular.module('app')
  .controller('appController', ['$scope', '$compile', function ($scope, $compile) {
      var data = {
          article : '<h1>hi</h1>'
      }
      $scope.data = data;
  }]).directive('ngHtmlCompile',function ($compile) {
      return function(scope, element, attrs) {
          scope.$watch(
            function(scope) {
               // watch the 'compile' expression for changes
              return scope.$eval(attrs.ngHtmlCompile);
            },
            function(value) {
              // when the 'compile' expression changes
              // assign it into the current DOM
              element.html(value);

              // compile the new DOM and link it to the current
              // scope.
              // NOTE: we only compile .childNodes so that
              // we don't get into infinite loop compiling ourselves
              $compile(element.contents())(scope);
            }
        );
    };
});

example:

<div ng-app="app">
    <div ng-controller="appController">        
        <div ng-html-compile="data.article"></div>
    </div>
</div>
