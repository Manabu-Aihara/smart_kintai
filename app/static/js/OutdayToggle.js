const toggleButton = document.getElementById('outday-switch');
const userInfoTrs = document.getElementsByClassName('user-info-row');

const dateToday = document.getElementById('shadow-today');
const outdayColumns = document.getElementsByClassName('shadow-column1');
const switchOn = document.getElementById('outday-on');

const toggleSwitch = (outdayFlag) => {
  if (outdayFlag) {
    console.log(outdayFlag);
    for (let i = 0; i < userInfoTrs.length; i++) {
      console.log(outdayColumns[i].textContent);
      // true いない人
      if (outdayColumns[i].textContent > dateToday.textContent || outdayColumns[i].textContent == 'None') {
        // console.log(`${i}: unvisible`);
        userInfoTrs[i].style.display = "none";
      } else {
        // console.log(`${i}: visible`);
        userInfoTrs[i].style.display = "table-row";
      }
    }
  } else {
    console.log(outdayFlag);
    for (let i = 0; i < userInfoTrs.length; i++) {
      console.log(outdayColumns[i].textContent);
      // false まだいる人
      if (outdayColumns[i].textContent > dateToday.textContent || outdayColumns[i].textContent == 'None') {
        // console.log(`${i}: visible`);
        userInfoTrs[i].style.display = "table-row";
      } else {
        // console.log(`${i}: unvisible`);
        userInfoTrs[i].style.display = "none";
      }
    }
  }
}

let displayFlag = true;
toggleButton.addEventListener('click', () => {
  // console.log('On click!');
  if (displayFlag == false) {
    toggleSwitch(displayFlag);
    switchOn.style.display = 'none';
    displayFlag = true;
    // toggleButton.style.color = 'red';
  } else {
    toggleSwitch(displayFlag);
    switchOn.style.display = 'block';
    displayFlag = false;
    // toggleButton.style.color = 'gray';
  }
});
