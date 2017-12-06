app.controller('AccessManagerCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'ngDialog', 'callServerService', 'messagingService', 'toaster',
function($scope, $rootScope, $timeout, $log, ngDialog, callServerService, messagingService, toaster)
{
    $log.info('entered access manager ctrl');
    $scope.gridOptions = {};
    callServerService.read_privileges();

    $scope.get_authorized_users = function()
    {
        callServerService.call_server('admin/get_authorized_users').
        success(function(data)
        {
            $scope.authorized_users = data.authorized_users;
        });
    }

    $scope.get_authorized_users();

    $scope.role_class = function(r)
    {
        switch (r.role)
        {
            case 'DEVELOPER':
                cls = 'fa-cogs';
                break;
            case 'ACCESS_MANAGER':
                cls = 'fa-th';
                break;
            case 'ADMIN':
                cls = 'fa-star';
                break;
            case 'TESTER':
                cls = 'fa-certificate';
                break;
            case 'EDITOR':
                cls = 'fa-pencil';
                break;
            case 'COMMENTATOR':
                cls = 'fa-comment';
                break;
            case 'PHOTO_UPLOADER':
                cls = 'fa-camera';
                break;
            case 'CHATTER':
                cls = 'fa-group';
                break;
            case 'CHAT_MODERATOR':
                cls = 'fa-anchor';
                break;
            case 'TEXT_AUDITOR':
                cls = 'fa-shield';
                break;
            case 'DATA_AUDITOR':
                cls = 'fa-thumbs-up';
                break;
            case 'HELP_AUTHOR':
                cls = 'fa-life-saver fa-pencil';
                break;
            case 'ADVANCED':
                cls = 'fa-certificate';
                break;
        }
        if (r.active)
        {
            cls += ' is_active';
        }
        return cls;
    }

    $scope.toggle_membership = function(r, id)
    {
        r.id = id
        callServerService.call_server('admin/toggle_membership', r)
        .success(function(data)
        {
            for (u in $scope.authorized_users)
            {
                user = $scope.authorized_users[u];
                if (user.id==data.id)
                {
                    for (r in user.roles)
                    {
                        role = user.roles[r];
                        if (role.role==data.role)
                        {
                            role.active = data.active;
                            break;
                        }
                    }
                    break;
                }
            }
        });
    }

    $scope.add_or_update = function(user_data)
    {
        if (user_data)
        {
            $scope.curr_user = _.clone(user_data);
            $scope.curr_user_ref = user_data;
        }
        else
        {
            $scope.curr_user = {last_name: "", service_level: 'standard'}
        }
        $scope.dialog = ngDialog.open({
            template: 'add_or_update_template',
            scope: $scope
        });
    }
    
    $scope.get_customer_info = function(uid)
    {
        callServerService.call_server('admin/get_customer_info', {user_id: uid}).
        success(function(data)
        {
            $scope.customer_info = data.customer_info;
        });
    }
    
    $scope.display_customer_data = function(uid)
    {
        $scope.customer_info = {name: 'snoofkin'};
        $scope.get_customer_info(uid);
        $scope.dialog = ngDialog.open({
            template: 'display_customer_data',
            scope: $scope
        });
    }

    $scope.unlock_user = function(uid)
    {
        callServerService.call_server('admin/unlock_user', {user_id: uid}).
        success(
            function(result)
            {
                toaster.pop('success', '', 'The user can now login');
            }
        );
    }

    $scope.resend_verification_email = function(uid)
    {
        callServerService.call_server('admin/resend_verification_email', {user_id: uid}).
        success(
            function(result)
            {
                toaster.pop('success', '', 'Verification email was sent');
            }
        );
    }

    $scope.user_idx_by_id = function(uid)
    {
        for (var idx in $scope.authorized_users)
        {
            if ($scope.authorized_users[idx].id == uid)
            {
                return idx;
            }
        }
    }

    $scope.delete_user = function(usr)
    {
        $scope.user_to_delete = usr;
        ngDialog.openConfirm({
            template: 'delete_user_template',
            scope: $scope
        }).
        then(function()
        {
            callServerService.call_server('admin/delete_user', usr).
            success(function(data)
            {
                var uid = parseInt(data.id);
                var idx = $scope.user_idx_by_id(data.id);
                $scope.authorized_users.splice(idx, 1);
            });
        });
    }

    $scope.save = function()
    {
        callServerService.call_server('admin/add_or_update_user', $scope.curr_user)
        .success(function(data)
        {
            if (data.error || data.user_error)
            {
                return;
            }                    
            if (data.new_user)
            {
                $scope.authorized_users.push(data.user_data);
            }
            else $timeout(function()
            {
                for (f in data.user_data)
                {
                    $scope.curr_user_ref[f] = data.user_data[f];
                }
            });
            $timeout(function()
            {
                $scope.dialog.close('good');
            });
        });            
    }
}
]);
