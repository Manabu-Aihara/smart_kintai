// 大本のセレクトボックス
const selectArea = document.getElementsByClassName('form-control')[0];
const startDayArea = document.getElementsByClassName('notice-day')[0];

let globalFlag = false;
const blurArea = (event, other) => {
  // console.log(event.currentTarget.parentNode);
  if (event.currentTarget.value === "") {
    event.currentTarget.parentNode.classList.add('field-invalid');
    globalFlag = false;
    return globalFlag;
  } else {
    event.currentTarget.parentNode.classList.remove('field-invalid');
    const invalidComp = document.getElementsByClassName('field-invalid');
    // console.log(`--${other.value}--`);
    if (other.value !== "" && invalidComp.length === 0) {
      globalFlag = true;
    }
    return globalFlag;
  }
}

selectArea.addEventListener('blur', (e) => blurArea(e, startDayArea));
startDayArea.addEventListener('blur', (e) => blurArea(e, selectArea));
