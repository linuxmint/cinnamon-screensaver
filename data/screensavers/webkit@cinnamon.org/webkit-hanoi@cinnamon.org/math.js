function rand(min, max, precision){
    if(!max){
        max = min;
        min = 0;
    }
    precision = precision || 1;
    return floor(Math.random() * (max - min + 1), precision) + min;
}

function floor(number, precision){
    precision = precision || 1;
    number -= number % precision;
    return parseFloat(number.toPrecision(12));
}

function round(n, p){
    p = p || 1;
    if(n % p >= p / 2) n += p;
    n -= n % p;
    return parseFloat(n.toPrecision(12));
}

var fround = Math.fround;

function ceil(n, p){
    p = p || 1;
    n += p;
    n -= n % p;
    return parseFloat(n.toPrecision(12));
}

function pow(n, e){
    return Math.pow(n, e || 2);
}

function abs(n){
    if(n < 0) return -n;
    else return n;
}

function min(){
    for(var i = 1, r = 0, l = arguments.length; i < l; ++i)
        if(arguments[i] < arguments[r]) r = i;
    return arguments[r];
}

function max(){
    for(var i = 1, r = 0, l = arguments.length; i < l; ++i)
        if(arguments[i] > arguments[r]) r = i;
    return arguments[r];
}

function less(){
    for(var i = 1, l = arguments.length; i < l; ++i)
        if(arguments[i - 1] >= arguments[i]) return false;
    return true;
}

function lequal(){
    for(var i = 1, l = arguments.length; i < l; ++i)
        if(arguments[i - 1] > arguments[i]) return false;
    return true;
}

function anyequal(a){
    for(var i = 1, l = arguments.length; i < l; ++i)
        if(a == arguments[i]) return true;
    return false;
}

function sin(deg){
    return Math.sin(deg * RAD);
}

function cos(deg){
    return Math.cos(deg * RAD);
}

var PI = Math.PI;
var TAU = PI * 2;
var RAD = PI / 180;
