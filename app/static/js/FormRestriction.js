// お前はもう、宣言されている
// const selectArea = document.getElementsByClassName('form-control')[0];
const selectChildren = selectArea.options;

// 開始時刻・終了時刻
const timeForms = document.getElementsByClassName('restrict-form');
// 入力制限処理トグル関数
const toggleRestrictState = (flag) => {
  if (flag == true) {
    for (let i = 0; i < timeForms.length; i++) {
      timeForms[i].readOnly = true;
      timeForms[i].style.backgroundColor = "gainsboro";
    }
  } else {
    for (let i = 0; i < timeForms.length; i++) {
      timeForms[i].readOnly = false;
      timeForms[i].style.backgroundColor = "";
    }
  }
}

const startTimeForm = timeForms[0];
const endTimeForm = timeForms[1];

// 半休用
const workTime = document.getElementById('worktime');

const separateTime = () => {
  let hourSide, minuteSide;
  halfTime = workTime.value / 2;
  // 時間
  hourSide = Math.floor(halfTime);
  // 分
  minuteSide = halfTime - Math.floor(halfTime);
  minuteSide = minuteSide * 60;
  return [hourSide, minuteSide];
}

// 半休用
const carryUpTime = (startTimeMinute) => {
  const [hourSide, minuteSide] = separateTime();
  integerMinute = Number(startTimeMinute);
  console.log(`***${startTimeMinute}+${minuteSide}***`);
  if (integerMinute + minuteSide >= 60) {
    console.log("繰り上げ");
    return [hourSide + 1, integerMinute + minuteSide - 60];
  } else {
    console.log("繰り上げなし");
    return [hourSide, integerMinute + minuteSide];
  }
}

// Param: diffNum 何時間後
const reflectTimeForm = (diffNum) => {
  /**
 * input type=date:値の変更の感知にはinput
 */
  startTimeForm.addEventListener('input', () => {
    let [h, m] = startTimeForm.value.split(':');
    /**
     * 半休
     * plus_m: startTimeFormのminutesと+workTimeの半分のminutes
     * plus_h: plus_mによって、繰り上げの可能性がある
     */
    diffNum === 0 ? [plus_h, plus_m] = carryUpTime(m) : [plus_h = 0, plus_m = m];

    if (h < 10 || plus_m < 10) {
      const oneDigit = Number(h) + diffNum + Number(plus_h);
      /**
       * 数字を指定した桁数まで0埋めする
          https://gray-code.com/javascript/fill-numbers-with-zeros/
      */
      endTimeForm.value = `${oneDigit.toString().padStart(2, '0')}:${plus_m.toString().padStart(2, '0')}`;
    } else {
      endTimeForm.value = `${oneDigit}:${plus_m}`;
    }
  });
}

const restrictCollection = () => {
  console.log(selectChildren.selectedIndex);

  console.log(selectChildren);
  if ((selectChildren.selectedIndex) === 4 || (selectChildren.selectedIndex) === 6 || (selectChildren.selectedIndex) === 8 || (selectChildren.selectedIndex) === 9 || (selectChildren.selectedIndex) === 17 || (selectChildren.selectedIndex) === 18 || (selectChildren.selectedIndex) === 19 || (selectChildren.selectedIndex) === 20) {
    toggleRestrictState(true);
  } else if ((selectChildren.selectedIndex) === 10 || (selectChildren.selectedIndex) === 13) {
    toggleRestrictState(false);
    reflectTimeForm(1);
  } else if ((selectChildren.selectedIndex) === 11 || (selectChildren.selectedIndex) === 14) {
    toggleRestrictState(false);
    reflectTimeForm(2);
  } else if ((selectChildren.selectedIndex) === 12 || (selectChildren.selectedIndex) === 15) {
    toggleRestrictState(false);
    reflectTimeForm(3);
    // 半休
  } else if ((selectChildren.selectedIndex) === 5 || (selectChildren.selectedIndex) === 7) {
    toggleRestrictState(false);
    reflectTimeForm(0)
  } else {
    toggleRestrictState(false);
  }
}

selectArea.addEventListener('change', restrictCollection);
