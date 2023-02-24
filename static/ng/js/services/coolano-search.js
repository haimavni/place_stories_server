app.factory('coolanoSearch', [function($rootScope){

	var service = {
		searches : [],
		current : false,
		resetSearch : function(){
			this.current = {
				title : 'All the eggs in one basket',
				description : 'Here will be a short description of the search e.g. "finding out events in Europe"',
				num_results : 1345,
				last_update : '29/jan/14 12:00',
				last_update_results : 7,
				next_update : '30/jan/14 12:00',
				next_update_status : 'Queued',
				keywords : [
					{ label : 'keyword1', count : 9 },
					{ label : 'keyword2', count : 7 },
					{ label : 'keyword3', count : 5 },
					{ label : 'keyword4', count : 4 },
					{ label : 'keyword5', count : 2 },
					{ label : 'keyword6', count : 1 }
				],
				feedback : {
					positive : 403,
					negative : 23
				},
				sources : [
					{ name : 'web', label : 'Web', count : 9 },
					{ name : 'facebook', label : 'Facebook', count : 7 },
					{ name : 'twitter', label : 'Twitter', count : 6 },
					{ name : 'instagram', label : 'Instagram', count : 5 },
					{ name : 'youtube', label : 'YouTube', count : 3 }
				]
			};
		},
		findSearch : function(id){
			alert('find search ' + id);
			$rootScope.$broadcast('searchIdChanged');

		},
		getSearchList : function(filters){

		},
		langs : [
			{
				code : 'en',
				label : 'English'
			},
			{
				code : 'ge',
				label : 'German'
			},
			{
				code : 'ru',
				label : 'Russian'
			},
			{
				code : 'fr',
				label : 'French'
			},
			{
				code : 'it',
				label : 'Italian'
			},
			{
				code : 'sp',
				label : 'Spanish'
			}
		],
		sources : [
			{
				label : 'Web',
				value : 'web'
			},
			{
				label : 'Facebook',
				value : 'facebook'
			},
			{
				label : 'Twitter',
				value : 'twitter'
			},
			{
				label : 'Instagram',
				value : 'instagram'
			},
			{
				label : 'Youtube',
				value : 'youtube'
			}
		]
	};

		return service;

}]);

