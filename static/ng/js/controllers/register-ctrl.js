app.controller('RegisterCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, callServerService, messagingService, toaster)
    {
        $log.info('entered clear register ctrl');
        $scope.user_info = {daily_email: true};
        var lst = window.location.href.split('?');
        if (lst.length > 1)
        {
            var vars = lst[lst.length-1];
            vars = vars.split('&');
            for (var v in vars)
            {
                var pair = vars[v].split('=');
                $scope.user_info[pair[0]] = pair[1];
            }
        }
        if ($scope.user_info.code)
        {
            $scope.user_info.referred = true;
        }
        $scope.verify_password_ascii = function()
        {
            if (! isASCII($scope.user_info.password))
            {
                $scope.user_info.password = $scope.user_info.password.slice(0, -1);
                alert('Illegal character!');
            }
        }

    $scope.register_user = function()
    {
        var u = $scope.user_info;
        if (!u.email || !u.password  || !u.first_name || !u.last_name)
        {
            toaster.pop('warning', 'Incomplete data', '<br><h4>Mandatory data missing!</h4>', 60000, 'trustedHtml');
            return;
        }
        if (u.password != $scope.password2)
        {
            toaster.pop('warning', 'Password confirmation', '<br><h4>Repeated password does not match!</h4>', 60000, 'trustedHtml');
            return;
        }
        searchParamsService.call_server('default/register_user', {user_info: $scope.user_info}).
        success(function(result)
        {
            if (result.good)
            {
                $scope.email_sent = 'email_sent';
            }
        });
    }
}
]);