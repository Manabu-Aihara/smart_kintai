//idが「boxes」の要素を取得
let tbl = document.getElementById("fav-body");
let tbody = table.firstElementChild

//行追加
function add(){

  

   //先頭にある子要素を複製（コピー）
  let clone = tbl.firstElementChild.cloneNode(true);

   //最後尾に複製した要素を追加
  tbl.appendChild(clone); 
  
  //先頭行が非表示なので、表示に戻す
  tbl.lastElementChild.style.display = "table-row";

  
}

//末尾行削除
function del(){
   
  let rw = tbl.rows.length;
  tbl.deleteRow(rw-1);
  
}

function delRow(o)
{
    var tr = o.parentNode.parentNode
	tr.parentNode.deleteRow(tr.sectionRowIndex);

}

function ErrorCheck()
{
	alert("メールアドレスを入力してください");


}