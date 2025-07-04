class ModalAppear {

  /* ModalFadeクラスのコンストラクタ */
  // @param under 下地
  // @param top モーダルウィンドウ
  // @param button モーダル表示ボタン
  // @param form ボタン内包フォーム
  constructor(under, top, button, form) {
    this.bottom_item = under;
    this.top_item = top;
    this.button_item = button;
    this.form = form;

    let myself = this;

    const appearModalSubmit = (dialog_phrase, modal_phrase) => {
      // globalFlag: ValidationCheck.jsより
      if (globalFlag === true) {
        console.log(globalFlag);
        if (window.confirm(`${dialog_phrase}宜しいですか？`)) {
          setTimeout(function () {
            myself.bottom_item.style.opacity = ".5";
            myself.top_item.style.visibility = "visible";
            let modal_p = myself.top_item.children;
            modal_p[0].innerText = modal_phrase;
            myself.form.submit();
          }, 700);
        } else {
          return false;
        }
      } else {
        alert("入力必須項目があります。");
      }
    }

    const formPath = /approval-form$/;
    this.callModal = function (arg1, arg2) {
      myself.button_item.addEventListener('click', (e) => {
        e.preventDefault();
        if (formPath.test(location.pathname)) {
          // selectArea, startDayArea: ValidationCheck.jsより
          blurArea(e, startDayArea) ? blurArea(e, selectArea) : globalFlag = false;
          // blurArea(e, selectArea) ? blurArea(e, startDayArea) : globalFlag = false;
        }
        appearModalSubmit(arg1, arg2);
      });
    }
  }
}