on("ready", function(){
    var canvas = elem("canvas");

    var ctx = canvas.getContext("2d");
    ctx.save();

    function setCanvasSize(){
        canvas.width = innerWidth;
        canvas.height = innerHeight;

        ctx.restore();
        ctx.save();

        ctx.translate(.25 * innerWidth, .9 * innerHeight);
        ctx.scale(.25 * innerWidth, -.8 * innerHeight);
    }

    setCanvasSize();
    on("resize", setCanvasSize);

    var n = 1;
    var colors = ["#F00", "#F80", "#FF0", "#8F0", "#0F0", "#0FF", "#08F", "#00F", "#80F", "#F08"];
    var pegs = [[1], [], []];
    var moving = null;
    var height = .2;
    var step = 0;

    var TIME = 1000;

    function doLegalMove(a, b){
        var pa = pegs[a];
        var pb = pegs[b];

        var da = pa[pa.length - 1];
        var db = pb[pb.length - 1];

        if(da < db || !db){
            moving = {
                m: da,
                destination: pb,
                t: now(),

                x: a,
                dx: b - a,

                y: (pa.length - 1) * height,
                dy: (pb.length + 1 - pa.length) * height
            };
            pa.pop();
        } else {
            moving = {
                m: db,
                destination: pa,
                t: now(),

                x: b,
                dx: a - b,

                y: (pb.length - 1) * height,
                dy: (pa.length + 1 - pb.length) * height
            };
            pb.pop();
        }
    }

    function drawDisk(m, x, y, height){
        var width = m / n * .5 + .25;

        ctx.fillStyle = colors[(m - 1) % colors.length];
        ctx.fillRect(x - width / 2, y, width, height);
    }

    function main(){
        ctx.clearRect(-1, -.5, 4, 2);

        if(step === -1)
            var x = ease.quadInOut(now() - moving.t, 2, -2, TIME);

        for(var i = 0, j, m; i < 3; ++i){
            for(j = 0, l = pegs[i].length; j < l; ++j){
                m = pegs[i][j];

                if(step === -1){
                    if(j === 0)
                        drawDisk(m, x, 0, height * (n % 1));
                    else
                        drawDisk(m, x, (j - 1 + n % 1) * height, height);
                } else
                    drawDisk(m, i, j * height, height);
            }
        }

        if(moving){
            if(step === -1){
                if(now() - moving.t > TIME){
                    n = moving.n + 1;
                    moving = null;
                    height = min(1 / n, .2);
                    pegs[0] = pegs[2];
                    pegs[2] = [];
                    step = 0;
                    TIME *= .75;
                } else {
                    n = ease.quadInOut(now() - moving.t, moving.n, 1, TIME);
                    height = min(1 / n, .2);
                }
            } else {
                if(now() - moving.t > TIME){
                    drawDisk(moving.m, moving.x + moving.dx, moving.y + moving.dy, height);
                    moving.destination.push(moving.m);
                    moving = null;
                } else {
                    var x = ease.cubicInOut(now() - moving.t, moving.x, moving.dx, TIME);
                    if(moving.dy < 0)
                        var y = ease.expoIn(now() - moving.t, moving.y, moving.dy, TIME);
                    else
                        var y = ease.expoOut(now() - moving.t, moving.y, moving.dy, TIME);

                    drawDisk(moving.m, x, y, height);
                }
            }
        } else {
            if(pegs[2].length === n){
                step = -1;
                pegs[2].splice(0, 0, n + 1);
                moving = {
                    n: n,
                    t: now()
                };
            } else if(step === 0){
                step = 1;

                if(n % 2)
                    doLegalMove(0, 2);
                else
                    doLegalMove(0, 1);
            } else if(step === 1){
                step = 2;
                if(n % 2)
                    doLegalMove(0, 1);
                else
                    doLegalMove(0, 2);
            } else if(step === 2){
                step = 0;
                doLegalMove(1, 2);
            }
        }

        requestAnimationFrame(main);
    }

    requestAnimationFrame(main);
});
