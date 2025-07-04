$(function () {
    var ua = navigator.userAgent;
    if ((ua.indexOf('iPhone') > 0) || ua.indexOf('iPod') > 0 || (ua.indexOf('Android') > 0 && ua.indexOf('Mobile') > 0)) {
        $('head').prepend('<meta name="viewport" content="width=device-width,initial-scale=1">');
    } else {
        $('head').prepend('<meta name="viewport" content="width=1050">');
    }
});

// ページリロードスクロール位置保持
/*
$('#sbmt').submit(function () {
    sessionStorage.scrollTop = $('#scrl').scrollTop();
    alert('保存しました！');
});

window.onload = function () {
    if (sessionStorage.scrollTop != "undefined") {
        $('#scrl').scrollTop(sessionStorage.scrollTop);
    }
    alert('保存しました！');
}
*/

/*
document.getElementsByClassName('go-back').addEventListener('click', () => {
    history.back();
});
*/

/*
$('form.scrl').submit(function () {
    var scroll_top = $(window).scrollTop();
    $('input.st', this).prop('value', scroll_top);
});

window.onload = function () {
    $(window).scrollTop(<? php echo @$_REQUEST['scroll_top']; ?>);
}
*/