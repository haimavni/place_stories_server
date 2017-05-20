app.controller('UserCtrl', ['$scope', '$timeout', '$window', 'callServerService', 'messagingService', 'toaster',
function($scope, $timeout, $window, callServerService, messagingService, toaster)
    {
        $scope.user_email = null;
        $scope.password = null;
        callServerService.translate($scope, {password: 'Password', login: 'Log In', cancel:'Cancel', please_login: 'Please Login', 
                                             email_address: "Email Address", register: "register", reset_password: "Reset Password",
                                             to_complete: 'To complete your registration, please check your email inbox.',
                                             if_you_dont: 'If you do not find email from us, check your spam box.',
                                             close: 'Close', first_name: 'First Name', last_name: 'Last Name',
                                             confirm_password: 'Confirm Password',
                                             please_register: 'Please Register'
        })

        $scope.do_login = function() 
        {
            callServerService.call_server('default/login', {user_email: $scope.user_email, password: $scope.password})
            .success(function(result)
            {
                if (result.error)
                {
                    good = false;
                }
                else
                {
                    callServerService.read_privileges();
                    good = true;
                }
                if (good)
                {
                    $scope.login_dialog.close('good');
                }
            });
        };
    
        $scope.logout = function()
        {
            callServerService.call_server('default/logout')
            .success(function(result)
            {
                callServerService.read_privileges();
            });
        };
        
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
            callServerService.call_server('default/register_user', {user_info: $scope.user_info}).
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

