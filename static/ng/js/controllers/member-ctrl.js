app.controller('MemberCtrl', ['$scope', '$rootScope', '$timeout', '$log', 'ngDialog', 'callServerService', 'messagingService', 'toaster',
    function($scope, $rootScope, $timeout, $log, ngDialog, callServerService, messagingService, toaster)
    {
        $log.info('entered member ctrl');
        $scope.texts_dic = {life_story: 'Life Story of', parents: 'Parents', spouses: 'Spouses', siblings: 'Siblings', 
            children: 'Children', member_card: 'Member Card',
            date_of_birth: 'Date of Birth', date_of_death: 'Date of Death', former_name: 'Former Name', member_name: 'Member Name',
            family_connections: 'Family Connections', birth_place: 'Birth Place', alia_date: 'Alia Date', 
            membership_date: 'Membership Date', first_name: 'First Name', former_first_name: 'Former First Name', nick_name: 'Nick Name',
            last_name: 'Last Name', former_last_name: 'Former Last Name', father_name: 'Father Name', mother_name: 'Mother Name',
            birth_place: 'Birth Place', select_member_photo: 'Select member representative photo', start_typing_name: 'Start typing name',
            identify_member: 'Identify member', identify_object: 'Identify object', not_identified_yet: 'Not identified yet!'};
        callServerService.translate($scope, $scope.texts_dic);
        $scope.parents_finder = {pa_filter: '', ma_filter: ''};
        $scope.person_finder = {filter: ''};
        $scope.member_info = {};
        $scope.family = {};
        $scope.identify_object = false;
        $scope.member_list = function()
        {
            if ($scope.parents_finder.pa_filter || $scope.parents_finder.ma_filter)
            {
                return $scope.item_list;
            }
            else
            {
                return [];
            }
        }

        $scope.handle_member = function(member_id, shift)  //shift is one of prev, self(none) or next
        {
            //$scope.member_id = member_id;
            if (shift)
            {
                //todo: if dirty, ask user to save or cancel before moving
            }
            $scope.check_dirty = false;
            callServerService.call_server('stories/get_member_info', {member_id: member_id, shift: shift})
            .success(function(data)
            {
                $scope.has_item['members'] = true;
                $scope.dirty = false;
                $scope.member_info = data.member_info;
                $scope.story_info = data.story_info;
                $scope.family = data.family_connections;
                $scope.images = data.images;
                $scope.vm = {};
                $scope.vm.slides = data.slides;
                $scope.vm.open = false;
                $scope.vm.opts = {index: 1};
                $scope.member_photo = $scope.images[0];
                $scope.dummy_face_path = data.dummy_face_path;
                $scope.set_member_photo($scope.member_info.member_photo_id);
                $scope.display_version = data.story_info ? data.story_info.display_version : '';
                $scope.face_info = {};
                //$scope.parents_finder.pa_filter = $scope.family.parents.pa.full_name;
                if ($scope.family.parents)
                {
                    $scope.parents_finder.pa_filter = $scope.family.parents.pa ? $scope.family.parents.pa.full_name : '';
                    $scope.parents_finder.ma_filter = $scope.family.parents.ma ? $scope.family.parents.ma.full_name : '';
                }
                else
                {
                    $scope.parents_finder.pa_filter = '';
                    $scope.parents_finder.ma_filter = '';
                }
                $scope.original_member_info = JSON.stringify($scope.member_info);
                $scope.check_dirty = true;
                $scope.refresh_dirty();
            });
        };
        
        $scope.toggle_member_object = function()
        {
            $scope.identify_object = ! $scope.identify_object;
        }
        
        $scope.next_slide = function(event)
        {
            event.stopPropagation();
            var n = $scope.vm.slides.length;
            $scope.vm.opts.index += 1;
            if ($scope.vm.opts.index == n)
            {
                $scope.vm.opts.index = 0;
            }
        }
        
        $scope.prev_slide = function(event)
        {
            event.stopPropagation();
            var n = $scope.vm.slides.length;
            if ($scope.vm.opts.index == 0)
            {
                $scope.vm.opts.index = n;
            }
            $scope.vm.opts.index -= 1;
        }
        
        $scope.expand_slide = function()
        {
            var slide = $scope.vm.slides[$scope.vm.opts.index];
            $scope.slide_path = slide.src;
            $scope.get_faces(slide.photo_id);
            $scope.slide_background_url = '{background: url(' + $scope.slide_path + ') no-repeat center center;height:100%}';
            
            $scope.expanded_slide = ngDialog.open(
            {
                template: BASE_APP_URL + 'static/ng/templates/expanded_photo.html',
                scope: $scope,
                width: "100%",
                height: "100%",
                opacity: "1.0",
                className: "ngdialog-theme-default ngdialog-fullscreen"
            });
        }
                
        $scope.get_faces = function(photo_id)
        {
            $scope.vm.faces = [];
            callServerService.call_server('stories/get_faces', {photo_id: photo_id})
            .success(function(data)
            {
                $scope.vm.faces = data.faces;
            });
        }
        
        $scope.mark_face = function(event)
        {
            if (! $rootScope.actively_editing)
            {
                return;
            }
            var photo_id = $scope.vm.slides[$scope.vm.opts.index].photo_id;
            var face = {photo_id: photo_id, x: event.offsetX, y: event.offsetY, r: 20};
            $scope.vm.faces.push(face);
            callServerService.call_server('stories/add_face', {face: face});
        }
        
        $scope.place_face = function(face)
        {
            var d = face.r * 2;
            return {left: (face.x - face.r) + 'px', 
                    top: (face.y - face.r) + 'px', 
                    width: d + 'px',
                    height: d + 'px',
                    position: 'absolute'};
        }
        
        $scope.jump_to_member = function(member_id)
        {
            event.stopPropagation();
            if (! member_id)
            {
                toaster.pop('warning', $scope.T.not_identified_yet, '', 2000);
                return;
            }
            $scope.expanded_slide.close();
            $timeout(function()
            {
                $scope.handle_member(member_id);
            });
        }
        
        $scope.handle_face = function(face, event)
        {
            event.stopPropagation();
            if (! $rootScope.actively_editing)
            {
                $scope.jump_to_member(face.member_id);
                return;
            }
            var resizing = true;
            if (event.ctrlKey)
            {
                face.r += 5;
            }
            else if (event.shiftKey)
            {
                if (face.r > 15)
                {
                    face.r -= 5;
                }
                else
                {
                    face.r = 0;
                    $scope.remove_face(face);
                }
            }
            else
            {
                resizing = false;
            }
            if (resizing)
            {
                callServerService.call_server('stories/resize_face', {face: face});
                return;
            }
            $scope.face_info.face = face;
            $scope.finder_dialog = ngDialog.open(
            {
                template: BASE_APP_URL + 'static/ng/templates/find_person.html',
                scope: $scope,
                width: "15%",
                height: "80%",
                opacity: "1.0",
                className: "ngdialog-theme-default"
            });

        }
        
        $scope.remove_face = function(face)
        {
            for (var i in $scope.vm.faces)
            {
                f = $scope.vm.faces[i];
                if (f.x == face.x && f.y == face.y)
                {
                    $scope.vm.faces.splice(i, i+1);
                    return;
                }
            }
        }
        
        $scope.identify_face = function(person)
        {
            $scope.person_finder.filter = '';
            callServerService.call_server('stories/identify_face', {person: person, face: $scope.face_info.face});
            $scope.finder_dialog.close();
        }
                
        $scope.toggle_full_screen = function(index)
        {
            $(this).css({width: 1000, height: 1000});
        }

        $scope.set_member_photo = function(photo_id)
        {
            for (var i in $scope.images)
            {
                var image = $scope.images[i]
                if (image.id == photo_id)
                {
                    $scope.member_photo = $scope.images[i];
                    $scope.member_info.member_photo_id = photo_id;
                    return;
                }
            }
            $scope.member_photo = {id: 0, path: $scope.dummy_face_path};
        }

        $scope.dirty = false;

        $scope.visibility_class= function()
        {
            if ($scope.member_info)
            {
                return $scope.member_info.visible ? "fa-eye" : "fa-eye-slash";
            }
            else
            {
                return '';
            }
        }
 
        $scope.refresh_dirty = function()
        {
            if (! $scope.check_dirty)
            {
                return;
            }
            var old_dirty = $scope.dirty;
            $scope.dirty = JSON.stringify($scope.member_info) != $scope.original_member_info;
            var dirty = $('#life_story').froalaEditor('undo.canDo');
            $scope.dirty = $scope.dirty || dirty;
            $timeout(function()
            {
                $scope.refresh_dirty();
            }, 1000);
        }
        
        $scope.add_member = function(data)
        {
            $scope.member_info = {
                last_name: '',
                FormerName: '',
                last_name: '',
                FormerName: '',
                 Name: '',
                PageHits: 0,
                NickName: '',
                first_name: '',
                visible: false,
                former_last_name: '',
                former_first_name: ''
                };
                $scope.story_info = {
                display_version: 'New Story', 
                story_versions: [], 
                story_text: '', 
                story_id: 0
            };
            $scope.images = [];
            $scope.member_photo = undefined;
            $scope.original_member_info = JSON.stringify($scope.member_info);
            $scope.check_dirty = true;
            $scope.handle_editing({command: 'start'});
            $scope.family = {};
        }
        
        $scope.save_member_info = function()
        {
            callServerService.call_server('stories/save_member_info', {member_info: $scope.member_info}).
            success(function(data)
            {
                $scope.original_member_info = JSON.stringify($scope.member_info);
                $scope.check_dirty = true;
            });
        }
        
        $scope.handle_editing = function(data)
        {
            var options =
            {
                language: 'he',
                toolbarButtons: ['undo', 'redo', '|', 'bold', 'italic', 'underline', '|', 'insertLink', 'insertImage', 'insertVideo', 'insertFile', '|',
                                 'selectAll', 'emoticons', 'color',  'fontFamily', 'fontSize', 'html']
            };
            switch(data.command)
            {
                case "start":
                    $(function()
                    {
                        $('#life_story').froalaEditor(options);
                        $scope.original_story = $('#life_story').froalaEditor('html.get', true);
                        $scope.refresh_dirty();
                    });
                    break;
                case "save":
                    var dirty = $('#life_story').froalaEditor('undo.canDo');
                    if (dirty)
                    {
                        var story_content = $('#life_story').froalaEditor('html.get', true);
                        $scope.story = story_content;
                        story_content = story_content.replace(/\&/g, '~1').replace(/;/g, '~2');
                        var story_info = 
                        {
                            story_text: story_content, 
                            story_id: $scope.story_info.story_id
                        };
                        callServerService.call_server('stories/save_story', {story_info: story_info}).
                        success(function(data)
                        {
                            if ($scope.dirty)
                            {
                                $scope.member_info.story_id = data.story_id;  //for new stories, saving member info must wait for story id
                                $scope.save_member_info()
                            }
                        });
                    }
                    else if ($scope.dirty)
                    {
                        callServerService.call_server('stories/save_member_info', {member_info: $scope.member_info}).
                        success(function(data)
                        {
                            $scope.original_member_info = JSON.stringify($scope.member_info);
                            $scope.check_dirty = true;
                        });
                    }
                    break;
                case "cancel":
                    $scope.member_info = JSON.parse($scope.original_member_info);
                    $('#life_story').froalaEditor('html.set', $scope.original_story);
                    break;
                case "stop":
                    $('#life_story').froalaEditor('destroy');
                    //todo: what to do if dirty?
                    break;
               }
        }
                
        $scope.toggle_gender = function()
        {
            if ($scope.member_info.gender == 'F')
            {
                $scope.member_info.gender = 'M'
            }
            else if ($scope.member_info.gender == 'M')
            {
                $scope.member_info.gender = 'F'
            }
            else
            {
                $scope.member_info.gender = 'F'
            }
        }
        
        $scope.show_mas_list = function()
        {
            var to_show = $scope.parents_finder.ma_filter;
            if ($scope.family && $scope.family.parents && $scope.family.parents.ma)
            {
                to_show = to_show && $scope.parents_finder.ma_filter != $scope.family.parents.ma.full_name;
            }
            return to_show
        }
        
        $scope.show_pas_list = function()
        {
            var to_show = $scope.parents_finder.pa_filter;
            if ($scope.family && $scope.family.parents && $scope.family.parents.pa)
            {
                to_show = to_show && $scope.parents_finder.pa_filter != $scope.family.parents.pa.full_name;
            }
            return to_show
        }
        
        $scope.filter_pa_by_name = function(rec)
        {
            var filter = $scope.parents_finder.pa_filter.replace('(', '').replace(')', '');
            if (filter.length == 0)
            {
                return false;
            }
            if (rec.gender != 'M' && rec.gender != 'F')
            {
                return false;  //for debugging.
            }
            if (!rec.id)  //special record for adding new member
            {
                return true;
            }
            if (rec.gender != 'M')
            {
                return false;
            }
            if ($scope.member_info.id == rec.id)
            {
                return false;
            }
            var name = rec.full_name;
            var lst = filter.split(" ");
            for (var i in lst)
            {
                if (! name.match(lst[i]))
                {
                    return false;
                }
            }
            return true;
        };
                
        $scope.filter_ma_by_name = function(rec)
        {
            if (!rec.id)  //special record for adding new member
            {
                return true;
            }
            if (rec.gender != 'F')
            {
                return false;
            }
            if ($scope.member_info.id == rec.id)
            {
                return false;
            }
            var name = rec.full_name;
            var filter = $scope.parents_finder.ma_filter.replace('(', '').replace(')', '');
            var lst = filter.split(" ");
            for (var i in lst)
            {
                if (! name.match(lst[i]))
                {
                    return false;
                }
            }
            return true;
        };
               
        $scope.filter_members_by_name = function(rec)
        {
            //words that the user marked as "in" or "out" are not filtered out
            var name = rec.name;
            var lst = $scope.person_finder.filter.split(" ");
            for (var i in lst)
            {
                if (! name.match(lst[i]))
                {
                    return false;
                }
            }
            return true;
        };  
        
        $scope.set_father = function(father_rec)
        {
            $scope.member_info.father_id = father_rec.id;
            $scope.parents_finder.pa_filter = father_rec.full_name; 
        }
    
        $scope.set_mother = function(mother_rec)
        {
            $scope.member_info.mother_id = mother_rec.id;
            $scope.parents_finder.ma_filter = mother_rec.full_name; 
        }
        
        $scope.next_version = function()
        {
        }
    
        $scope.prev_version = function()
        {
        }
    
        $scope.prev_member = function()
        {
            if ($scope.dirty)
            {
                alert('You have unsaved changes');
                return;
            }
            $scope.handle_member($scope.member_info.id, 'prev');
        }
            
        $scope.next_member = function()
        {
            if ($scope.dirty)
            {
                alert('You have unsaved changes');
                return;
            }
            $scope.handle_member($scope.member_info.id, 'next');
        }
            
        messagingService.register('members', $scope.handle_member);
        messagingService.register('members-editing', $scope.handle_editing);
        messagingService.register('members-add', $scope.add_member);
        
        $scope.photo_selected = function(photo_id)
        {
            return photo_id == $scope.member_info.member_photo_id ? 'photo-selected' : 'photo-unselected';
        }
        
        $scope.handle_member_list_change = function(data)
        {
             if (data.new_member)
             {
                var n = $scope.item_list.length;
                $scope.item_list.push(data.member_rec);
                $scope.item_index[data.member_rec.id] = n;
             }
             else
             {
                var i = $scope.item_index[data.member_rec.id];
                var rec = $scope.item_list[i];
                Object.keys(data.member_rec).forEach(function(key, idx)
                {
                    rec[key] = data.member_rec[key];
                });
             }
        }
        
        messagingService.register('MEMBER_LISTS_CHANGED', $scope.handle_member_list_change);
        
    }
]);
