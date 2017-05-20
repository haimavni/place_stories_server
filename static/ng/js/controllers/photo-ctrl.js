app.controller('PhotoCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, callServerService, messagingService, toaster)
    {
        $log.info('entered photo ctrl');
        $scope.handle_photo = function(photo_id)
        {
            $scope.photo_id = photo_id;
            callServerService.call_server('stories/get_photo_info', {photo_id: photo_id})
            .success(function(data)
            {
                $scope.photo_info = data.photo_info;
                $scope.story_info = data.story_info;
            });
        };
        messagingService.register('photos', $scope.handle_photo);
     }
]);
