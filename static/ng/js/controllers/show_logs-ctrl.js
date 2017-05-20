app.controller('ShowLogsCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, callServerService, messagingService, toaster)
    {
        $log.info('entered show logs ctrl');
        callServerService.read_privileges($scope);

        $scope.gridOptions = {};
        
        $scope.get_file_list = function()
        {
            callServerService.call_server('developer/log_file_list')
                .success(function(data)
                {
                    $scope.log_files = data.log_files;
                });
        }
        
        $scope.get_file_list();
        
        $scope.show_log_file = function(file_name)
        {
            $scope.displayed_log_file = file_name;
            callServerService.call_server('developer/log_file_data', {file_name: file_name})
                .success(function(data)
                {
                    $scope.log_html = data.log_html;
                });
        }
        
        $scope.delete_log_file = function(file_name)
        {
            callServerService.call_server('developer/delete_log_file', {file_name: file_name})
                .success(function(data)
                {
                    for (var i in $scope.log_files)
                    {
                        if ($scope.log_files[i].fn == file_name)
                        {
                            $scope.log_files.splice(i, 1);
                        }
                    }
                });
        }
        
        $scope.download_log_file = function(file_name)
        {
            callServerService.call_server('developer/download_log_file', {file_name: file_name})
                .success(function(data)
                {
                    window.location = 'download_file/' + data.file_path;
                });
        }
        
    }
]);