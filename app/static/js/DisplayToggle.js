const displaySelect = document.getElementById('display-toggle');
const userInfoTrs = document.getElementsByClassName('user-info-row');
const displayItems = document.getElementsByClassName('shadow-item');

const toggleDisplay = (selectState) => {
  console.log(`Select state: ${selectState}`);
  if (selectState === '表示') {
    for (i = 0; i < userInfoTrs.length; i++) {
      // console.log(`Display flag: ${displayItems[i].textContent}`)
      if (displayItems[i].textContent === 'False') {
        userInfoTrs[i].style.display = 'table-row';
      } else {
        userInfoTrs[i].style.display = 'none';
      }
    }
  } else if (selectState === '非表示') {
    for (i = 0; i < userInfoTrs.length; i++) {
      if (displayItems[i].textContent === 'True') {
        userInfoTrs[i].style.display = 'table-row';
      } else {
        userInfoTrs[i].style.display = 'none';
      }
    }
  }
}

displaySelect.addEventListener('change', () => {
  toggleDisplay(displaySelect.value);
});

window.addEventListener('load', toggleDisplay('表示'));
