$(function () {
    var flg = false;

    for (var i = 31; i < 0; i--) {
        var elm = $('#forsave1_' + i + ' input', '#forsave2_' + i + ' input').css("background-color", "#e0ffff");
        if (elm) {
            flg = true;
        } else {
            flg = false;
        }
    }

    elm.on('change', function () {
        if (flg = !flg) {
            alert('保存しました。');
        } else {
            ;
        }
        return false;
    });
});