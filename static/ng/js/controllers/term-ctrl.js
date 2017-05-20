app.controller('TermCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, callServerService, messagingService, toaster)
    {
        $log.info('entered term ctrl');
        $scope.handle_term = function(term_id)
        {
            $scope.term_id = term_id;
            callServerService.call_server('stories/get_term_info', {term_id: term_id})
            .success(function(data)
            {
                $scope.term_info = data.term_info;
                $scope.story_info = data.story_info;
            });
        };
        messagingService.register('terms', $scope.handle_term);
    }
]);
