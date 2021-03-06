onload = function(){
    face_rect(true);
    document.getElementById("facemode").onclick = function(){
        face_rect(this.checked);
    }
};

$('#detailtab a').click(function (e) {
  e.preventDefault()
  $(this).tab('show')
})

function face_rect(mode) {
    var canvas = document.getElementById('image_canvas');
    if ( ! canvas || ! canvas.getContext ) {
        return false;
    }
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0,0,canvas.width,canvas.height);
    var img = new Image();
    img.src = image_url;
    img.onload = function() {
        canvas.setAttribute("width", img.width.toString());
        canvas.setAttribute("height", img.height.toString());
        ctx.drawImage(img, 0, 0);
        if(mode){
            ctx.beginPath();
            ctx.strokeStyle = 'rgb(00,255,00)';
            ctx.lineWidth = 3;
            for(var i = 0; i < eval(facex).length; i++){
                var rectx = Number(eval(facex)[i]);
                var recty = Number(eval(facey)[i]);
                var rectw = Number(eval(facew)[i]);
                var recth = Number(eval(faceh)[i]);
                ctx.strokeRect(rectx,recty,rectw,recth);
            }
        }
    }
}