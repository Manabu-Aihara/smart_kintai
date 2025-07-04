/*
$(function () {
    $('hlf').on('change', function () {
        var converted = $(this).val().replace(/[０-９]/g, function (s) { // (1)
            return String.fromCharCode(s.charCodeAt(0) - 65248); // (2)
        });
        $(this).val(converted);
    });
})
*/

var zen2han = function (e) {
    var v, old = e.value;
    return function () {
        if (old != (v = e.value)) {
            old = v;
            var str = $(this).val();
            str = str.replace(/[０-９]/g, function (s) {
                return String.fromCharCode(s.charCodeAt(0) - 65248);
            });
            while (str.match(/[^０-９^0-9\.]/g)) {
                str = str.replace(/[^０-９^0-9\.]/g, "");
            }
            $(this).val(str);

        }
    }
};
$(function () {
    $("#half").each(function () {
        $(this).bind('keyup', zen2han(this));
    });
});