app.controller('EventCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, callServerService, messagingService, toaster)
    {
        $log.info('entered event ctrl');
        $scope.handle_event = function(event_id)
        {
            $scope.event_id = event_id;
            callServerService.call_server('stories/get_event_info', {event_id: event_id})
            .success(function(data)
            {
                $scope.event_info = data.event_info;
                $scope.story_info = data.story_info;
            });
        };
        messagingService.register('events', $scope.handle_event);
    }
]);
