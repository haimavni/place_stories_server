#!/bin/bash

pushd /home/haim/dist_software
target=/home/haim/fossil_projects/gbs/static/lib
cp bower_components/jquery/dist/jquery.min.js ${target}/
cp bower_components/jquery/dist/jquery.min.map ${target}/
cp bower_components/jquery-ui/jquery-ui.min.js ${target}/
cp bower_components/lodash/dist/lodash.js ${target}/
cp bower_components/angular/angular.min.js ${target}/
cp bower_components/angular/angular.min.js.map ${target}/
cp bower_components/angular-route/angular-route.min.js ${target}/
cp bower_components/angular-route/angular-route.min.js.map ${target}/
cp bower_components/angular-sanitize/angular-sanitize.min.js ${target}/
cp bower_components/angular-sanitize/angular-sanitize.min.js.map ${target}/
cp bower_components/angular-animate/angular-animate.min.js ${target}/
cp bower_components/angular-animate/angular-animate.min.js.map ${target}/
cp bower_components/angular-resource/angular-resource.min.js ${target}/
cp bower_components/angular-resource/angular-resource.min.js.map ${target}/
cp bower_components/flow.js/dist/flow.js ${target}/
cp bower_components/flow.js/dist/flow.min.js ${target}/
cp bower_components/angular-bootstrap/ui-bootstrap-tpls.min.js ${target}/
cp bower_components/bootstrap/dist/js/bootstrap.min.js ${target}/
cp bower_components/bootstrap/dist/css/bootstrap.min.css ${target}/
cp bower_components/angular-json-human/dist/angular-json-human.min.js ${target}/
cp bower_components/angular-json-human/dist/angular-json-human.min.css ${target}/
cp bower_components/AngularJS-Toaster/toaster.js ${target}/
cp bower_components/AngularJS-Toaster/toaster.css ${target}/
cp bower_components/font-awesome/css/font-awesome.min.css ${target}/
cp bower_components/font-awesome/fonts/* ${target}/../fonts
cp bower_components/angular-bootstrap/ui-bootstrap-tpls.min.js ${target}/
cp bower_components/tr-ng-grid/trNgGrid.min.js ${target}/
cp bower_components/tr-ng-grid/trNgGrid.min.css ${target}/
cp bower_components/ng-dialog/js/ngDialog.min.js ${target}/
cp bower_components/ng-dialog/css/ngDialog.min.css ${target}/
cp bower_components/ng-dialog/css/ngDialog-theme-default.min.css ${target}/
cp bower_components/angular-ui-select/dist/select.min.js ${target}/
cp bower_components/angular-ui-select/dist/select.min.css ${target}/
popd

