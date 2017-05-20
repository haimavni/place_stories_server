js_utils = {};

function compare_nums(a, b)
{
    return a - b;
}

js_utils.emit_sorted_num = function(obj)
{
    var keys = [];
    for (var k in obj)
    {
        keys.push(parseInt(k));
    }
    keys.sort(compare_nums);
    var result = [];
    for (var k in keys)
    {
        result.push(obj[keys[k]])
    }
        return result;
}

js_utils.flatten_obj = function(obj)
{
    var result = [];
    for (var i in obj)
    {
        result.push(obj[i])
    }
    return result;
}

jQuery.fn.cssInt = function (prop) {
    return parseInt(this.css(prop), 10) || 0;
};


jQuery.fn.cssFloat = function (prop) {
    return parseFloat(this.css(prop)) || 0;
};

function onload(doc)
{
    var x = this;
    alert('bla');
}

var popupWindows = {};
popup = function(key, url, params)
{
    var hnd = popupWindows[key];
    if (hnd)
    {
        hnd.close();
    }
    var w = popupWindows[key] = window.open(url, '_blank', params);
    var d = w.document;
    $(d).bind('onloadeddata', onload);
    return w
}

function isASCII(str)
{
    return /^[\x00-\x7F]*$/.test(str);
}

function closeCurrentWindow()
{
    window.location = 'http://www.coolano.com';
    //chrome.windows.remove(window.id)
}

function displayTime() 
{
    var str = "";

    var currentTime = new Date()
    var hours = currentTime.getHours()
    var minutes = currentTime.getMinutes()
    var seconds = currentTime.getSeconds()

    if (minutes < 10) 
    {
        minutes = "0" + minutes
    }
    if (seconds < 10) 
    {
        seconds = "0" + seconds
    }
    str += hours + ":" + minutes + ":" + seconds + " ";
    if(hours > 11)
    {
        str += "PM"
    } 
    else 
    {
        str += "AM"
    }
    return str;
}

function deep_copy(obj)
{
    //todo: make it be deep indeed
    var result = {};
    for (f in obj)
    {
        result[f] = obj[f];
    }
    return result;
}

function escapeRegExp(str) 
{
    return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}


escape = function (str) {
  return str
    .replace(/[\\]/g, '\\\\')
    .replace(/[\"]/g, '\\\"')
    .replace(/[\/]/g, '\\/')
    .replace(/[\b]/g, '\\b')
    .replace(/[\f]/g, '\\f')
    .replace(/[\n]/g, '\\n')
    .replace(/[\r]/g, '\\r')
    .replace(/[\t]/g, '\\t');
};