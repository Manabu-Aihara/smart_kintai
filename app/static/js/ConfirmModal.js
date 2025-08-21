const noticeForm = document.getElementById('delete-user');
const confirmModal = document.getElementById('confirm-modal');

const hideModal = () => {
  confirmModal.style.visibility = "hidden";
}

const appearModal = () => {
  setTimeout(function () {
    confirmModal.style.visibility = "visible";
    // confirmModal.style.opacity = "1";
  }, 300);
}

const appearButton = document.getElementById('ask-delete');
appearButton.addEventListener('click', appearModal);
const submitButton = document.getElementById('on-submit');
submitButton.addEventListener('click', () => {
  noticeForm.submit();
})
const hideButton = document.getElementById('on-hide');
hideButton.addEventListener('click', hideModal);
