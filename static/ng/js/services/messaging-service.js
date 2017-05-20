app.factory('messagingService', [function(){

    var service = 
    {
        listeners: {},

        register: function(key, action)
        {
            if (!this.listeners[key]) 
            {
                this.listeners[key] = [];
            }
            this.listeners[key].push(action);
        },
    
        notify: function(key, data)
        {
            for (var who in this.listeners[key])
            {
                this.listeners[key][who](data);
            }
        }
        
        
    };

    return service;

}]);

