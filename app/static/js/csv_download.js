// テーブルデータのCSVダウンロード
function onCSVDownload(a, table, filename) {
    var escaped = /,|\r?\n|\r|"/;
    var e = /"/g;

    // データ作成
    var bom = new Uint8Array([0xEF, 0xBB, 0xBF]); // UTF-8BOMあり
    var csv = [], row = [], field, r, c;
    for (r = 0; r < table.rows.length; r++) {
        row.length = 0;
        for (c = 0; c < table.rows[r].cells.length; c++) {
            field = (table.rows[r].cells[c].textContent).replace(/\r?\s+/g, ""); // 変数 = 変数.replace(/\r?\n/g,"");
            row.push(escaped.test(field) ? '"' + field.replace(e, '""') + '"' : field);
            // 区切り、改行、エスケープ文字を含む場合、エスケープ文字文字で囲む（エスケープ文字は二重にする）
        }
        csv.push(row.join(','));
    }
    //var blob = new Blob([/*bom, */csv.join('\n')], {'type': 'text/csv'}); // BOMなし
    var blob = new Blob([bom, csv.join('\n')], { 'type': 'text/csv' });

    // 保存
    if (window.navigator.msSaveBlob) {
        // IE用(保存 or 開く保存)
        window.navigator.msSaveBlob(blob, filename);
        //window.navigator.msSaveOrOpenBlob(blob, filename);
    } else {
        a.download = filename;
        a.href = window.URL.createObjectURL(blob);
    }
}