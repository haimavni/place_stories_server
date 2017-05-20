app.controller('EditorCtrl', ['$scope', '$rootScope', '$timeout', '$log', '$sce', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, $sce, callServerService, messagingService, toaster)
    {
        $log.info('entered editor ctrl');
        handle_editor_start = function(input)
        {
            $scope.story_text = $sce.trustAsHtml(input.story);
                    $(function()
                    {
                        $('#edit_story').css({'background-color': 'yellow'});
                        $('#edit_story').froalaEditor(
                        {
                            language: 'he'
                        });
                    });
        }
        $scope.edit_me = function()
        {
            var boom = $('#edit_story').froalaEditor(
            {
                language: 'he'
            });
            var x = $('#edit_story').froalaEditor('html.get', true);
        }
         messagingService.register('editor-start', handle_editor_start);
     }
]);
