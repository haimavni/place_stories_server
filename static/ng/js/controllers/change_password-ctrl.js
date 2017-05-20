app.controller('ChangePasswordCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'searchParamsService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, searchParamsService, messagingService, toaster)
    {
        $log.info('entered change password ctrl');
        $scope.user_info = {};
        $scope.verify_password_ascii = function()
        {
            if (! isASCII($scope.user_info.password))
            {
                $scope.user_info.password = $scope.user_info.password.slice(0, -1);
                alert('Illegal character!');
            }
        }

        $scope.change_password = function()
        {
            var u = $scope.user_info;
            if (!u.old_password  || !u.new_password)
            {
                toaster.pop('warning', 'Incomplete data', '<br><h4>Mandatory data missing!</h4>', 60000, 'trustedHtml');
                return;
            }
            if (u.new_password != $scope.password2)
            {
                toaster.pop('warning', 'Password confirmation', '<br><h4>Repeated password does not match!</h4>', 60000, 'trustedHtml');
                return;
            }
            searchParamsService.call_server('default/do_change_password', {user_info: $scope.user_info}).
            success(function(result)
            {
                if (result.good)
                {
                    toaster.pop('success', 'Password Change', '<br><p>Your password has been changed</p>', 30000, 'trustedHtml');
                    $timeout(function()
                    {
                        window.close();
                    }, 5000);
                }
            });
        }
    }
]);