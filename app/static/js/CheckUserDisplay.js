const appearanceSelect = document.getElementById('display-toggle');
// お前はもう、宣言されている
// const userInfoTrs = document.getElementsByClassName('user-info-row');

const displayColumns = document.getElementsByClassName('shadow-column2');

const getAppearanceFlag = () => {
  // const selectIndex = appearanceSelect.options.selectedIndex;
  // const displayJudge = appearanceSelect.options[selectIndex].innerText;
  // console.log(displayJudge);
  const optionList = appearanceSelect.selectedOptions;
  return optionList;
}

const showRowByCheckUsers = () => {
  options = getAppearanceFlag();
  for (let i = 0; i < userInfoTrs.length; i++) {
    if (displayColumns[i].textContent == options[0].value) {
      userInfoTrs[i].style.display = "none";
    } else {
      userInfoTrs[i].style.display = "table-row";
    }
  }
}

appearanceSelect.addEventListener('change', showRowByCheckUsers);
