//t: current time, b: beginning value, c: change in value, d: duration
var ease = {
    linear: function(t, b, c, d){
        return c * t / d + b;
    },
    step: function(t, b, c, d, s){
        if(t == d) return c + b;
        s = s || 10;
        return floor(t, d / s) / d * c + b;
    },
    bezier: function(t, b, c, d, s){
        if(!(s instanceof Array)) s = [.25, .1, .25, 1];
        var name = "bezier_" + s.join("_").replace(/\./g, "p").replace(/-/, "m");
        if(typeof ease[name] !== "function"){
            var polyBez = function(p){
                var a = [null, null], b = [null, null], c = [null, null];
                var o = function(t, i){
                    c[i] = 3 * p[i], b[i] = 3 * (p[i + 2] - p[i]) - c[i], a[i] = 1 - c[i] - b[i];
                    return t * (c[i] + t * (b[i] + t * a[i]));
                };
                var f = function(t){
                    var x = t, i = 0, z;
                    while(++i < 14){
                        z = o(x, 0) - t;
                        if(abs(z) < .001) break;
                        x -= z / (c[0] + x * (2 * b[0] + 3 * a[0] * x));
                    }
                    return x;
                };
                return function(t){
                    return o(f(t), 1);
                }
            };
            ease[name] = function(t, b, c, d){
                return c * polyBez(s)(t / d) + b;
            };
        }
        return ease[name](t, b, c, d);
    },
    ease: function(t, b, c, d){
        return ease.bezier(t, b, c, d, [.25, .1, .25, 1]);
    },
    easeIn: function(t, b, c, d){
        return ease.bezier(t, b, c, d, [.42, 0, 1, 1]);
    },
    easeOut: function(t, b, c, d){
        return ease.bezier(t, b, c, d, [0, 0, .58, 1]);
    },
    easeInOut: function(t, b, c, d){
        return ease.bezier(t, b, c, d, [.42, 0, .58, 1]);
    },
    quadIn: function(t, b, c, d){
        return c * (t /= d) * t + b;
    },
    quadOut: function(t, b, c, d){
        return -c *(t /= d) * (t - 2) + b;
    },
    quadInOut: function(t, b, c, d){
        if((t /= d / 2) < 1) return c / 2 * pow(t) + b;
        return -c / 2 * (--t * (t - 2) - 1) + b;
    },
    cubicIn: function(t, b, c, d){
        return c * (t /= d) * pow(t) + b;
    },
    cubicOut: function(t, b, c, d){
        return c * ((t = t / d - 1) * pow(t) + 1) + b;
    },
    cubicInOut: function(t, b, c, d){
        if((t /= d / 2) < 1) return c / 2 * pow(t, 3) + b;
        return c / 2 * ((t -= 2) * pow(t) + 2) + b;
    },
    quartIn: function(t, b, c, d){
        return c * (t /= d) * pow(t, 3) + b;
    },
    quartOut: function(t, b, c, d){
        return -c * ((t = t / d - 1) * pow(t, 3) - 1) + b;
    },
    quartInOut: function(t, b, c, d){
        if ((t /= d / 2) < 1) return c / 2 * pow(t, 4) + b;
        return -c / 2 * ((t -= 2) * pow(t, 3) - 2) + b;
    },
    quintIn: function(t, b, c, d){
        return c * (t /= d) * pow(t, 4) + b;
    },
    quintOut: function(t, b, c, d){
        return c * ((t =  t / d - 1) * pow(t, 4) + 1) + b;
    },
    quintInOut: function(t, b, c, d){
        if((t /= d / 2) < 1) return c / 2 * pow(t, 5) + b;
        return c / 2 * ((t -= 2) * pow(t, 4) + 2) + b;
    },
    sineIn: function(t, b, c, d){
        return -c * Math.cos(t / d * PI / 2) + c + b;
    },
    sineOut: function(t, b, c, d){
        return c * Math.sin(t / d * PI / 2) + b;
    },
    sineInOut: function(t, b, c, d){
        return -c / 2 * (Math.cos(PI * t / d) - 1) + b;
    },
    expoIn: function(t, b, c, d){
        return t == 0? b : c * pow(2, 10 * (t / d - 1)) + b;
    },
    expoOut: function(t, b, c, d){
        return t == d? b + c : c * (-pow(2, -10 * t / d) + 1) + b;
    },
    expoInOut: function(t, b, c, d){
        if(t == 0) return b;
        if(t == d) return b + c;
        if((t /= d / 2) < 1) return c / 2 * pow(2, 10 * (t - 1)) + b;
        return c/2 * (-pow(2, -10 * --t) + 2) + b;
    },
    circIn: function(t, b, c, d){
        return -c * (Math.sqrt(1 - (t /= d) * t) - 1) + b;
    },
    circOut: function(t, b, c, d){
        return c * Math.sqrt(1 - (t = t / d - 1) * t) + b;
    },
    circInOut: function(t, b, c, d){
        if((t /= d / 2) < 1) return -c / 2 * (Math.sqrt(1 - pow(t)) - 1) + b;
        return c / 2 * (Math.sqrt(1 - (t -= 2) * t) + 1) + b;
    },
    elasticIn: function(t, b, c, d, s){
        var p = d * (s || .3), q = p / 4;
        if(t == 0) return b;
        if((t /= d) == 1) return b + c;
        return -(c * pow(2, 10 * (t -= 1)) * Math.sin((t * d - q) * TAU / p)) + b;
    },
    elasticOut: function(t, b, c, d, s){
        var p = d * (s || .3), q = p / 4;
        if(t == 0) return b;
        if((t /= d) == 1) return b + c;
        return c * pow(2, -10 * t) * Math.sin((t * d - q) * TAU / p) + c + b;
    },
    elasticInOut: function(t, b, c, d, s){
        if(t == 0) return b;
        if((t /= d / 2) == 2) return b + c;
        var p = d * (s || .2), q = p / 4;
        if(t < 1) return -.5 * (c * pow(2, 10 * (t -= 1)) * Math.sin((t * d - q) * TAU / p)) + b;
        return c * pow(2, -10 * (t -= 1)) * Math.sin((t * d - q) * TAU / p) * .5 + c + b;
    },
    backIn: function(t, b, c, d, s){
        return ease.bezier(t, b, c, d, [.6, -s, .73, .05]);
    },
    backOut: function(t, b, c, d, s){
        return ease.bezier(t, b, c, d, [.175, .885, .32, 1 + s]);
    },
    backInOut: function(t, b, c, d, s){
        return ease.bezier(t, b, c, d, [0.68, -s * 2, 0.265, 1 + s * 2]);
    },
    bounceIn: function(t, b, c, d, s){
        return c - ease.bounceOut(d - t, 0, c, d, s) + b;
    },
    bounceOut: function(t, b, c, d, s){
        s = s || 1;
        if((t /= d) < 1 / 2.75)
            return c * (7.5625 * t * t) + b;
        else if(t < 2 / 2.75)
            return c * (7.5625 * (t -= (3 / 2) / 2.75) * t + (1 - 1 / 4)) + b;
        else if(t < 2.5 / 2.75)
            return c * (7.5625 * (t -= (9 / 4) / 2.75) * t + (1 - 1 / 16)) + b;
        else
            return c * (7.5625 * (t -= (21 / 8) / 2.75) * t + (1 - 1 / 64)) + b;
    },
    bounceInOut: function(t, b, c, d, s){
        if(t < d / 2) return ease.bounceIn(t * 2, 0, c, d, s) * .5 + b;
        return ease.bounceOut(t * 2 - d, 0, c, d, s) * .5 + c * .5 + b;
    }
};

function animate(o, p, b, c, d, m, x, s, t){
    if(!t) t = (new Date()).getTime();
    var q = ((new Date()).getTime() - t) / 1000;
    if(q > d){
        o[p] = ease[m](d, b, c, d, s) + x;
        return;
    }
    else {
        o[p] = ease[m](q, b, c, d, s) + x;
        requestAnimationFrame(function(){
            animate(o, p, b, c, d, m, x, s, t);
        });
    }
}

HTMLElement.prototype.animate = function(p, b, c, d, m, x, s){
    animate(this, p, b, c, d, m, x, s);
}
CSS2Properties.prototype.animate = function(p, b, c, d, m, x, s){
    animate(this, p, b, c, d, m, x, s);
}
