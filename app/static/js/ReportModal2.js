
// お前はもう、宣言されている
// const bottomForm = document.getElementById('form-bottom');
const JudgeButton = document.getElementsByClassName('judgement');

globalFlag = true;
const ModalSubmit_ok = new ModalAppear(backArea[0], modalElement, JudgeButton[0], bottomForm[0]);
ModalSubmit_ok.callModal("承認します。", "承認されます。");
const ModalSubmit_ng = new ModalAppear(backArea[0], modalElement, JudgeButton[1], bottomForm[1]);
ModalSubmit_ng.callModal("未承認にします。", "未承認です。");
