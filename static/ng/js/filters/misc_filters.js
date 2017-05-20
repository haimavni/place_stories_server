app.filter('truncdate', function($filter)
{
    return function(input)
    {
        if(input == null)
        { 
            return ""; 
        } 

        var _date = input.substr(0, 10);

        return _date;

    };
});

app.filter('x_if_true', function($filter)
{
    return function(input)
    {
        return input ? "X" : ""
    };
});

