app.controller('ChatCtrl', ['$scope', 'callServerService', 'messagingService', '$timeout', function ($scope, callServerService, messagingService, $timeout)
{
    $scope.scroll_to_bottom = function()
    {
        var el = document.getElementById("scroll-area");
        el.scrollTop = 10000; //el.scrollHeight - el.scrollTop;
    }
    
    $scope.read_chatroom = function()
    {
        callServerService.call_server('stories/read_chatroom', {room_number: $scope.room_number})  //room number was injected onload in the html
        .success(function(data)
        {
            $scope.chatroom_name = data.chatroom_name;
            $scope.messages = data.messages;
        });
        $scope.info = {user_message: ''};
        callServerService.listen('CHATROOM' + $scope.room_number);
        messagingService.register('INCOMING_MESSAGE' + $scope.room_number, $scope.handle_incoming_message);
    }
    
    $scope.send_message = function()
    {
        callServerService.call_server('stories/send_message', {user_message: $scope.info.user_message, room_number: $scope.room_number, room_index: $scope.room_index})
        .success(function(data)
        {
            $scope.info.user_message = "";
        });
    };
    
    $scope.handle_incoming_message = function(msg)
    {
       $scope.messages.push(msg);
    };
    
    $scope.handle_selected = function()
    {
        $timeout(function()
        {
            $scope.scroll_to_bottom();
        });
    };
    messagingService.register('SELECTED-chat', $scope.handle_selected)
}]);

app.controller('ChatroomsCtrl', ['$scope', 'callServerService', function($scope, callServerService)
{
    callServerService.translate($scope, {chatroom: 'Chat Room', group: 'Discussion Group', chats: 'Chats',
                                         enter_search_words: 'Enter search words', send_message: 'Send message',
                                         enter_your_message: 'Enter your message'
                                        });
    $scope.chatrooms = [];
    $scope.first_chatroom_number = 0;
    $scope.chats_per_page = 4;
    $scope.new_chatroom_name_visible = false;
    $scope.new_chatroom_name = '';
    
    $scope.read_chatrooms = function()
    {
        callServerService.call_server('stories/read_chatrooms')
        .success(function(data)
        {
            $scope.chatrooms = data.chatrooms;
        });
    };
    
    $scope.read_chatrooms();
    
    $scope.add_chatroom = function()
    {
        if ($scope.new_chatroom_name)
        {
            callServerService.call_server('stories/add_chatroom', {new_chatroom_name: $scope.new_chatroom_name})
            .success(function(data)
            {
                var chatroom = {id: data.chatroom_id, messages: [], info: {user_message: ''}};
                $scope.chatrooms.push(chatroom);
                $scope.first_chatroom_number = $scope.chatrooms.length - 4;
                if ($scope.first_chatroom_number < 0)
                {
                    $scope.first_chatroom_number = 0;
                }
            });
            $scope.new_chatroom_name = '';
            $scope.new_chatroom_name_visible = false;
        }
        else
        {
            $scope.new_chatroom_name_visible = true;
        }
    };
    
    $scope.can_move_left = function()
    {
        return $scope.first_chatroom_number > 0
    }
    $scope.move_left = function()
    {
        if ($scope.can_move_left())
        {
            $scope.first_chatroom_number -= 1;
        }
    };
    
    $scope.can_move_right = function()
    {
        return $scope.first_chatroom_number < $scope.chatrooms.length - $scope.chats_per_page
    }
    $scope.move_right = function()
    {
        if ($scope.can_move_right())
        {
            $scope.first_chatroom_number += 1;
        }
    };
    
}]);