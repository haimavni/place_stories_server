app.controller('ClearCacheCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, callServerService, messagingService, toaster)
    {
        $log.info('entered clear cache ctrl');
        callServerService.read_privileges();

        $scope.gridOptions = {};
        
        $scope.read_cache_info = function()
        {
            callServerService.call_server('developer/read_cache_info')
                .success(function(data)
                {
                    $scope.cache_keys = data.cache_keys;
                });
        }
        
        $scope.read_cache_info();
        
        $scope.clear_cache_item = function(key)
        {
            callServerService.call_server('developer/clear_cache_item', {key: key})
                .success(function(data)
                {
                    for (var i in $scope.cache_keys)
                    {
                        if ($scope.cache_keys[i].key == key)
                        {
                            $scope.cache_keys.splice(i, 1);
                            break;
                        }
                    }
                });
        }
 
    }
]);