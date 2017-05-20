app.controller('MainCtrl', ['$scope', '$rootScope', '$http', '$timeout', '$location', '$window', 'ngDialog', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $http, $timeout, $location, $window, ngDialog, callServerService, messagingService, toaster)
    {
        $scope.fd = {
            names_filter: ''
        };
        $scope.state = {
            selected: 'main'
        };

        $scope.has_item = {};

        $scope.item_lists = {members: [], stories: [], terms: [], events: [], photos: []};
        $scope.item_indexes = {members: {}, stories: {}, terms:{}, events: {}, photos: {}};

        $scope.make_place_holders = function()
        {
            var place_holders_dict = {
                members: 'Type name, previous name or nick name',
                stories: 'Start typing story title',
                photos: 'Start typing photo caption',
                terms: 'Start typing term title',
                events: 'Start typing event title'
            }
            $scope.place_holders = {}
            callServerService.translate($scope.place_holders, place_holders_dict);
            callServerService.translate($scope, {edit: "Edit", view: "View"});
        };

        $scope.make_place_holders();

        $scope.item_class = function(what)
        {
            return what == $scope.state.selected ? 'm_selected' : ''
        }

        $scope.do_select = function(what)
        {
            $scope.state.selected = what;
            $scope.place_holder = $scope.place_holders.T[what];
            if ($scope.item_lists[what] && $scope.item_lists[what].length == 0)
            {
                $scope.get_item_list(what)
            }
            else
            {
                $scope.item_list = $scope.item_lists[what];
            }
            messagingService.notify('SELECTED-' + what)
        }

        callServerService.read_privileges($scope);
        callServerService.translate($scope, {upload_photos: 'Upload photos'});
        
        $scope.get_item_list = function(what)
        {
            callServerService.call_server('stories/get_item_list', {what: what})
            .success(function(data)
            {
                $scope.item_lists[what] = data.arr;
                $scope.item_indexes[what] = data.index;
                $scope.item_list = $scope.item_lists[what];
                $scope.item_index = $scope.item_indexes[what];
            });
        }

        $scope.get_item_info = function(item_id)
        {
            messagingService.notify($scope.state.selected, item_id);
            $scope.has_item[$scope.state.selected] = true;
            $scope.fd.names_filter = '';
        }

        $scope.filter_by_name = function(rec)
        {
            //words that the user marked as "in" or "out" are not filtered out
            var name = rec.name;
            var lst = $scope.fd.names_filter.split(" ");
            for (var i in lst)
            {
                if (! name.match(lst[i]))
                {
                    return false;
                }
            }
            return true;
        };
        
        $scope.selected_item_is_searchable = function()
        {
            var result = $scope.state.selected=='members' || 
                $scope.state.selected=='stories' || 
                $scope.state.selected=='photos' || 
                $scope.state.selected=='terms' || 
                $scope.state.selected=='events';
            return result
        }

        $scope.selected_item_is_editable = function()
        {
            return $scope.selected_item_is_searchable() && $scope.has_item[$scope.state.selected];
        }

        $scope.toggle_edit_mode = function()
        {
            $rootScope.actively_editing = ! $rootScope.actively_editing;
            messagingService.notify($scope.state.selected + '-editing', {command: $scope.actively_editing ? 'start' : 'stop'});
        }

        $scope.add_item = function()
        {
            $rootScope.actively_editing = true;
            messagingService.notify($scope.state.selected + '-add', {command: 'start'});
        }

        $scope.cancel_edit_mode = function()
        {
            //$rootScope.actively_editing = false;
            //re-read data
            messagingService.notify($scope.state.selected + '-editing', {command: 'cancel'})
        }

        $scope.save_edited_data = function()
        {
            //todo: according to state.selected, save edited data
            //$rootScope.actively_editing = false;
            messagingService.notify($scope.state.selected + '-editing', {command: 'save'});
        }

        $scope.register = function()
        {
            $scope.registration_dialog = ngDialog.open(
            {
                template: BASE_APP_URL + 'static/ng/templates/register.html',
                scope: $scope,
                controller: 'UserCtrl'
            });
        }

        $scope.login = function()
        {
            $scope.login_dialog = ngDialog.open(
            {
                template: BASE_APP_URL + 'static/ng/templates/login.html',
                scope: $scope,
                //className: 'ngdialog-theme-plain',
                controller: 'UserCtrl'
            });
        }

        $scope.upload_photos = function()
        {
            $scope.upload_dialog = ngDialog.open(
            {
                template: BASE_APP_URL + 'static/ng/templates/upload-page.html',
                scope: $scope,
                //className: 'ngdialog-theme-plain',
                controller: 'UploadCtrl'
            });
        }

        $scope.chat = function()
        {
            $scope.chat_dialog = ngDialog.open(
            {
                template: BASE_APP_URL + 'static/ng/templates/chat-page.html',
                scope: $scope,
                //height: "100%",
                //width: "30%",
                className: "ngdialog-theme-default ngdialog-chat",
                controller: 'ChatroomsCtrl'           
            });
        }
        
        callServerService.listen('ALL_USERS');        
        
        $scope.handle_role_change = function(data)
        {
            $rootScope.privileges[data.role] = data.active;
        }
        
        $scope.ad_hoc_script = function()
        {
            $scope.scripts_dialog = ngDialog.open(
            {
                template: APP + '/static/ng/templates/plugin-scripts-page.html',
                scope: $scope,
                className: 'ngdialog-theme-default ngdialog-scripts',
                controller: 'ScriptsCtrl'
            });
        }
        
        $scope.show_log_files = function()
        {
            $scope.scripts_dialog = ngDialog.open(
            {
                template: APP + '/static/ng/templates/show_logs-page.html',
                scope: $scope,
                className: 'ngdialog-theme-default ngdialog-scripts',
                controller: 'ShowLogsCtrl'
            });
        }
        
        messagingService.register('ROLE_CHANGED', $scope.handle_role_change);
        
    }
]);
