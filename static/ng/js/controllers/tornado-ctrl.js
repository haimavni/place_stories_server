app.controller('TornadoCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'ngDialog', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, ngDialog, callServerService, messagingService, toaster)
    {
        $scope.callback = function(e)
        {
            var obj = JSON.parse(e.data);
            var msg = obj.data.message;
            alert(msg)
        };
        $scope.message = "Hello Tornado";
        callServerService.call_server('default/get_tornado_host')
            .success(function(data)
            {
                $scope.ws = data.ws;
                if(!web2py_websocket($scope.ws, $scope.callback))
                {
                    alert("html5 websocket not supported by your browser, try Google Chrome");
                };
            });
        $scope.send = function()
        {
            callServerService.call_server('test_tornado/send', {message: $scope.message});
        }
    }
]);
