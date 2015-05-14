function obj(typ, object){
    object = object || {};
    typ.toLowerCase();
    switch(typ) {
        case "image":          var obj = new Image(); break;
        case "xhr":
        case "xmlhttprequest": if(window.XMLHttpRequest) var obj = new XMLHttpRequest(); break;
        case "audio":          var obj = new Audio(); break;
        default:               var obj = {}; break;
    }
    for(var i in object)
        obj[i] = object[i];
    return obj;
}
function img(src){
    var img = new Image();
    img.src = src;
    return img;
}

function xhr(url, arg){
    function query(obj){
        var str = "";
        for(var i in obj)
            str += (str == ""? "" : "&") + i + "=" + obj[i];
        return encodeURI(str);
    }
    var request = obj("xhr");

    if(arg instanceof Function) arg = {load: arg};

    if(arg.load){
        request.addEventListener("load", function(){
            arg.load(request.response, request);
        });
    }
    if(arg.progress){
        request.addEventListener("progress", function(evt){
            arg.progress(evt.lengthComputable? evt.loaded / evt.total : null, request);
        });
    }

    if(arg.method && arg.method == "POST"){
        request.open("POST", url, true);
        request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        request.send(query(arg.arg));
    } else {
        request.open(arg.method || "GET", url, true);
        request.send();
    }
}

function elem(r){
    if(r[0] == "<"){
        var n = document.createElement(r.substring(1, r.length - 1));
        var s = arguments[1] || {};
        var i, j;
        for(i in s){
            if(i == "css") i = "style";
            if(s[i] instanceof Object){
                for(j in s[i])
                    n[i][j] = s[i][j];
            } else
                n[i] = s[i];
        } 
        s = arguments[2] || {};
        for(i in s)
            n.addEventListener(i, s[i]);
        return n;
    } else
        return document.querySelector(r);
}

function elems(s){
    return document.querySelectorAll(s);
}

NodeList.prototype.forEach = Array.prototype.forEach;
Array.prototype = {
    get last(){
        return this[this.length - 1];
    }
};

function on(type, callback){
    if(type == "ready") type = "DOMContentLoaded";
    addEventListener(type, callback);
}

HTMLElement.prototype.on = function(type, callback){
    this.addEventListener(type, callback);
}

HTMLElement.prototype.elem = function(r){
    return this.querySelector(r);
}

HTMLElement.prototype.elems = function(r){
    return this.querySelectorAll(r);
}

HTMLElement.prototype.append = function(n){
    if(typeof n == "string") n = elem.apply(void 0, arguments);
    return this.appendChild(n);
}

HTMLElement.prototype.appendAfter = function(n, m){
    if(typeof n == "string") n = elem.apply(void 0, arguments);
    return m.nextElementSibling? this.insertBefore(n, m.nextElementSibling) : this.appendChild(n);
}

SVGSVGElement.prototype.append = function(n, a){
    if(typeof n == "string"){
        n = document.createElementNS("http://www.w3.org/2000/svg", n.substr(1, n.length - 2));
        for(var i in a){
            n.setAttribute(i, a[i]);
        }
    }
    return this.appendChild(n);
}

function now(){
    return performance.now();
}

function time(){
    return (new Date()).getTime();
}
