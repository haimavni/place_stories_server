app.factory('callServerService', ['$http', '$q', '$log', '$rootScope', '$window', 'toaster', 'messagingService',
    function($http, $q, $log, $rootScope, $window, toaster, messagingService)
    {
        var service = 
        {
            num_pending_calls: 0,

            call_server: function(url, params, options)  //url is actually controller/function
            {
                url = BASE_APP_URL + url;
                var options = options ? options : {}
                $log.info('call server ' + url + '. num-pending: ' + service.num_pending_calls);
                if (!options.quiet)
                {
                    service.num_pending_calls += 1;
                    if (service.num_pending_calls >= 1)
                    {
                        $rootScope.show_working = true;
                    }
                }
                var promise = $http(
                {
                    method: 'POST',
                    url: url,
                    params: params
                });

                promise.finally(function()
                {
                    if (options.quiet)
                    {
                        return;
                    }
                    service.num_pending_calls -= 1;
                    $log.info('Finished handling ' + url + '. Num pending: ' + service.num_pending_calls)
                    if (service.num_pending_calls == 0)
                    {
                        $rootScope.show_working = false;
                    }
                });

                promise.success(function(data)
                {
                    if (data.Location)
                    {
                        $window.location = data.Location;
                    }
                    if (data.errors)
                    {
                        var errors = data.errors;
                        var msg = '';
                        Object.keys(errors).forEach(function(key, idx)
                        {
                            msg += key + ': ' + errors[key] + '<br/>'
                        });
                        toaster.pop('warning', 'Attention!', msg, 60000, 'trustedHtml');
                    }
                    if (data.error) //exception was raised
                    {
                        toaster.pop('error', 'A server error occured at ' + displayTime() + '!', data.error, 60000, 'trustedHtml');
                        return $q.reject('error occured');
                    }
                    if (data.user_error) //user error detected and "user error" exception was raised. todo: see above "errors" for the better way.
                    {
                        toaster.pop('warning', 'Attention!', data.user_error, 60000, 'trustedHtml');
                        return $q.reject('error occured');
                    }
                    if (data.warning) //the call was completed, but there is a warning to display
                    {
                        toaster.pop('warning', 'Warning!', data.warning, 60000, 'trustedHtml');
                    }
                    if (data.success)
                    {
                        toaster.pop('success', 'Success', data.success, 5000, 'trustedHtml');
                    }
                    if (data.info)
                    {
                        toaster.pop('info', 'Info', data.info, 30000, 'trustedHtml');
                    }
                    if (options.next)
                    {
                        options.next()
                    }
                });

                promise.error(function(data)
                {
                    $log.error(data);
                    toaster.pop('error', 'An unhandled server error occured at ' + displayTime() + '!', data, 60000, 'trustedHtml');
                });
                return promise;
            },
        
            user_info: function()
            {
                return service.call_server('xxx/user_info', {})
            },
        
            read_privileges: function()
            {
                service.call_server('default/read_privileges').success(function(data)
                {
                    $rootScope.privileges = data.privileges;
                    $rootScope.emails_suspended = data.emails_suspended;
                    $rootScope.user_id = data.user_id;
                });
            },
            
            translate: function(scope, phrases)
            {
                service.call_server('default/translate', {phrases: phrases}).success(function(data)
                {
                    scope['T'] = data.translations;
                });
            },
            
            handle_ws_message: function(e)
            {
                var obj = JSON.parse(e.data);
                var key = obj.key;
                var data = obj.data;
                messagingService.notify(key, data);
            },
            
        };

        service.listen = function(group)
        {
            var x = window.location;
            service.call_server('default/get_tornado_host', {group: group})
            .success(function(data)
            {
                ws = data.ws;
                if(!web2py_websocket(ws, service.handle_ws_message))
                {
                    alert("html5 websocket not supported by your browser, try Google Chrome");
                };
            });
        };
        
        service.listen();  //by default, listen to USERx, where x is user id
        
         
        return service;
    }
]);
