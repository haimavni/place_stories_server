var app = angular.module('gbs', ['ngRoute', 'ngSanitize', 'ngResource', 'ngDragDrop', 'trNgGrid', 'ngDialog', 
                         'ui.bootstrap', 'ui.select', 'ngFileUpload',
                         'ngTouch', 'ngAnimate', 'regexValidateApp', 'toaster', 'yaru22.jsonHuman', 'luegg.directives']);

app.config(['$httpProvider', '$routeProvider', '$locationProvider',
    function($httpProvider, $routeProvider, $locationProvider){
        $httpProvider.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
        $httpProvider.defaults.transformRequest = function(data){
            if (data === undefined) {
                return data;
            }
            return $.param(data);
        };

    $locationProvider.html5Mode(true);
    }]
);

app.run(function()
{
    TrNgGrid.columnSortInactiveCssClass = "tr-ng-sort-inactive text-muted fa fa-chevron-down";
    TrNgGrid.columnSortReverseOrderCssClass = "tr-ng-sort-order-reverse fa fa-chevron-down";
    TrNgGrid.columnSortNormalOrderCssClass = "tr-ng-sort-order-normal fa fa-chevron-up";
});

app.directive('sortable', function() {
    return {
        // A = attribute, E = Element, C = Class and M = HTML Comment
        restrict:'A',
        link: function(scope, element, attrs) {
            element.sortable({
                connectWith: ".dropable"
            }).disableSelection();
        }
    }
});

app.directive('popover', function($timeout) {
    return {
        // A = attribute, E = Element, C = Class and M = HTML Comment
        restrict:'A',
        link: function(scope, element, attrs) {
            $(element).popover({
                html : true,
                content: function() {
                    var id = $(element).attr('id');
                    return $("#tag-content-" + id).html();
                }
            });
        }
    }
});

app.directive('backgroundImageDirective', function () {
    return function (scope, element, attrs) {
        element.css({
            'background-image': 'url(' + attrs.backgroundImageDirective + ')',
            'background-repeat': 'no-repeat',
        });
    };
});

app.filter('propsFilter', function() {
  return function(items, props) {
    var out = [];

    if (angular.isArray(items)) {
      items.forEach(function(item) {
        var itemMatches = false;

        var keys = Object.keys(props);
        for (var i = 0; i < keys.length; i++) {
          var prop = keys[i];
          var text = props[prop].toLowerCase();
          if (item[prop].toString().toLowerCase().indexOf(text) !== -1) {
            itemMatches = true;
            break;
          }
        }

        if (itemMatches) {
          out.push(item);
        }
      });
    } else {
      // Let the output be the input untouched
      out = items;
    }

    return out;
  };
});
