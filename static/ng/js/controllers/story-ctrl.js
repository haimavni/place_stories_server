app.controller('StoryCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, callServerService, messagingService, toaster)
    {
        $log.info('entered story ctrl');
        $scope.handle_story = function(story_id)
        {
            $scope.story_id = story_id;
            callServerService.call_server('stories/get_story_info', {story_id: story_id})
            .success(function(data)
            {
                $scope.story_info = data.story_info;
            });
        };
        messagingService.register('stories', $scope.handle_story);
     }
]);
