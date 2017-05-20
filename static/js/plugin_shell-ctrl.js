app.controller('PluginShellCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, callServerService, messagingService, toaster)
    {
        $log.info('entered plugin shell ctrl');
        callServerService.read_privileges($scope);

        $scope.gridOptions = {};
        
        $scope.load_script = function()
        {
            callServerService.call_server('load_script')
                .success(function(data)
                {
                    $scope.code = data.code;
                    $scope.prev_enabled = data.prev_enabled;
                    $scope.next_enabled = data.next_enabled
                });
        }
        
        $scope.load_script();
        
        $scope.evaluate_script = function(code)
        {
            callServerService.call_server('plugin_shell/evaluate_script', {code: $scope.code})
                .success(function(data)
                {
                    $scope.results = data.results;
                });
        }
        
        $scope.prev_code = function(code)
        {
            callServerService.call_server('plugin_shell/prev_code', {code: $scope.code, like: $scope.like})
                .success(function(data)
                {
                    $scope.code = data.code;
                    $scope.prev_enabled = data.prev_enabled;
                    $scope.next_enabled = data.next_enabled
                });
        }
        
        $scope.next_code = function(code)
        {
            callServerService.call_server('plugin_shell/next_code', {code: $scope.code, like: $scope.like})
                .success(function(data)
                {
                    $scope.code = data.code;
                    $scope.prev_enabled = data.prev_enabled;
                    $scope.next_enabled = data.next_enabled
                });
        }
        
        $scope.delete = function(code)
        {
            callServerService.call_server('plugin_shell/delete', {code: $scope.code, like: $scope.like})
                .success(function(data)
                {
                    $scope.code = data.code;
                    $scope.prev_enabled = data.prev_enabled;
                    $scope.next_enabled = data.next_enabled
                });
        }
   }
]);