app.controller('TaskMonitorCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'ngDialog', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, ngDialog, callServerService, messagingService, toaster)
    {
        $log.info('entered tasks monitor ctrl');
        callServerService.read_privileges($scope);
		callServerService.listen('TASK_MONITOR')
        $scope.gridOptions = {};

        $scope.handle_status_changed = function(data)
        {
            var task = null;
			var tsk = $scope.find_task(data.task_id);
			if (tsk >= 0)
			{
				task = $scope.task_list[tsk]
			}
            if (!task)
            {
                alert('task not found!')
                return;
            }
            $timeout(function()
            {
                for (var k in data.data)
                {
                    task[k] = data.data[k];
                }
            });
        }
        
        messagingService.register('task_status_changed', $scope.handle_status_changed);
    
        $scope.read_tasks = function()
        {
            callServerService.call_server('admin/read_tasks', {}).
            success(
                function(data)
                {
                    $scope.task_list = data.task_list;
                }
            );
        }
    
        $scope.read_tasks();
    
        $scope.restart_task = function(task_id)
        {
            callServerService.call_server('admin/restart_task', {task_id: task_id}).success(
            function(data)
            {
				//will be refreshed by message from the server
            });
        }
    
        $scope.stop_task = function(task_id)
        {
            callServerService.call_server('admin/stop_task', {task_id: task_id}).success(
            function(data)
            {
				//will be refreshed by message from the server
            });
        }
    
		$scope.find_task = function(task_id)
		{
			for (var t in $scope.task_list)
			{
				if ($scope.task_list[t].task_id == task_id)
				{
					return t;
				}
			}
			return -1;
		}
		
        $scope.delete_task = function(task_id)
        {
            callServerService.call_server('admin/delete_task', {task_id: task_id}).success(
            function(data)
            {
				var idx = $scope.find_task(task_id);
				$timeout(function()
				{
					$scope.task_list.splice(idx, 1);
				});
            });
        }
		
		$scope.remove_completed_tasks = function()
		{
			callServerService.call_server('admin/remove_completed_tasks').success(
			function(data)
			{
				$scope.read_tasks();
			});
		}
    }
]);
