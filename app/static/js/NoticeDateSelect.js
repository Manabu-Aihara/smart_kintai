const notificationDateList = document.getElementsByClassName('notice-date');
// お前はもう、宣言されている
// const yearMonthDate = document.getElementsByClassName('month-calender')[0];
// const trRows = document.getElementsByClassName('body-tr');

// 承認者閲覧pathname
const chargePath = /approval-list\/charge*$/;
const appearRows = document.getElementsByClassName('appear');

const showRowsByNotificationDate = () => {
  console.log(yearMonthDate.value);
  console.log(appearRows.length);
  for (let i = 0; i < appearRows.length; i++) {
    // console.log(appearRows[i].children[0].textContent.match(/^\d{4}-?\d{2}/)[0]);
    // ['2023-08', index: 0, input: '2023-08-17 10:17:04', groups: undefined]なので[0]
    if (appearRows[i].children[0].innerText.match(/^\d{4}-\d{2}/)[0] !== yearMonthDate.value) {
      // for (let j = 0; j < appearRows.length; j++) {
      appearRows[i].style.display = "none";
      // }
    } else {
      appearRows[i].style.display = "table-row";
    }

    if (yearMonthDate.value === "") {
      for (let i = 0; i < appearRows.length; i++) {
        appearRows[i].style.display = "table-row";
      }
    }
  }
}

yearMonthDate.addEventListener('change', showRowsByNotificationDate);

if (chargePath.test(location.pathname)) {
  window.addEventListener('load', () => {
    yearMonthDate.value = "";
  });
}
