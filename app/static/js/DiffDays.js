
let formDays = document.getElementsByClassName('notice-day');
const compareDays1 = () => {

  try {
    if(formDays[0].value > formDays[1].value){
      // throw new Error("開始日より前です。");
      alert("開始日より前です。");
      formDays[1].value = "";
      // exit();
    }
  } catch(e) {
    console.log(e);
  }
}

const compareDays2 = () => {
  // 本日の日付
  // https://www.ey-office.com/blog_archive/2023/04/18/short-code-to-get-todays-date-in-yyyy-mm-dd-format-in-javascript/
  const today = new Date().toLocaleDateString("ja-JP", {year: "numeric",month: "2-digit", day: "2-digit"}).replaceAll('/', '-');
  try {
    console.log(today);
    if (today >= formDays[0].value) {
      // throw new Error("前日の申請はできません。");
      alert("前日の申請はできません。");
      formDays[0].value = "";
    } else {
      return true;
    }
  } catch(e) {
    console.log(e);
  }
}

// formDays[0].addEventListener('change', compareDays2);
formDays[1].addEventListener('change', compareDays1);
