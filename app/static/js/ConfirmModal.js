const noticeForm = document.getElementById('approval');
const confirmModal = document.getElementById('confirm-modal');

const hideModal = () => {
    confirmModal.style.visibility = "hidden";
}

const appareModal = () => {
  setTimeout(function(){
    confirmModal.style.visibility = "visible";
    // confirmModal.style.opacity = "1";
  }, 300);
}

const appareButton = document.getElementsByClassName('btn-ask')[0];
appareButton.addEventListener('click', appareModal);
const submitButton = document.getElementById('on-submit');
submitButton.addEventListener('click', () => {
  noticeForm.submit();
})
const hideButton = document.getElementById('on-hide');
hideButton.addEventListener('click', hideModal);
