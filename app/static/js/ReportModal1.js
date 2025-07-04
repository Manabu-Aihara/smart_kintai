// お前はもう、宣言されている
// const modalElement = document.getElementsByClassName('modal')[0];
// const backArea = document.getElementsByClassName('disp')[0];
const noticeForm = document.getElementById('approval');

const askButton = document.getElementsByClassName('btn-ask')[0];

// class="disp"だけなぜ？
const ModalAndSubmit = new ModalAppear(backArea[0], modalElement, askButton, noticeForm);
ModalAndSubmit.callModal("申請します。この内容で", "申請しました。承認をお待ちください。");
