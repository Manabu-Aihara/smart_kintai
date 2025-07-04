// お前はもう、宣言されている
// const yearMonthDate = document.getElementsByClassName('month-calender')[0];
// const trRows = document.getElementsByClassName('body-tr');
const holidayTermSelect = document.getElementsByClassName('term-list')[0];
const startDayList = document.getElementsByClassName('rest-start');

const getAcquisitionDate = () => {
  const selectIndex = holidayTermSelect.options.selectedIndex;
  const combiDate = holidayTermSelect.options[selectIndex].innerText
  const regexMatch = combiDate.match(/(?<from>\d{4}-\d{2}-\d{2}) \| (?<to>\d{4}-\d{2}-\d{2})/);
  return [regexMatch.groups.from, regexMatch.groups.to];
}

// 申請一覧pathname
const tail_d = /\d+$/;

const showRowsByHolidayTermDate = () => {
  console.log(getAcquisitionDate()[1]);
  for (let i = 0; i < trRows.length; i++) {
    // console.log(startDayList[i].textContent.match(/^\d{4}-\d{2}-\d{2}/)[0]);
    // ['2023-08-17', index: 0, input: '2023-08-17 10:17:04', groups: undefined]なので[0]
    if (startDayList[i].textContent.match(/^\d{4}-\d{2}-\d{2}/)[0] >= getAcquisitionDate()[0] && startDayList[i].textContent.match(/^\d{4}-\d{2}-\d{2}/)[0] <= getAcquisitionDate()[1]) {
      trRows[i].style.display = "table-row";
    } else {
      trRows[i].style.display = "none";
    }

    // こいつが悪さをしてました
    // if (holidayTermSelect.options[0]) {
    //   for (let i = 0; i < trRows.length; i++) {
    //     trRows[i].style.display = "table-row";
    //   }
    // }
  }
}

holidayTermSelect.addEventListener('change', showRowsByHolidayTermDate);
