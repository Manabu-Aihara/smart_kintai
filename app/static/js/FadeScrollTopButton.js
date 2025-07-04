// const paginationArea = document.querySelector('.dataTables_paginate');
// console.log(paginationArea);
// 要素を取得
const toTopElm = document.getElementById("page-top-wrap");
// 初期状態で要素を透明にする
toTopElm.style.opacity = "0";

window.addEventListener('scroll', () => {
  const nowPosition = window.scrollY;
  // console.log('Height: ', nowPosition);
  if (nowPosition > 1500) {
    // フェードインのアニメーションを設定
    toTopElm.style.transition = "opacity 1s ease-in-out";
    toTopElm.style.opacity = "1";
  } else {
    toTopElm.style.transition = "opacity 1s ease-in-out";
    toTopElm.style.opacity = "0";
  }

  const toTopButton = document.getElementById("page-top-icon");
  toTopButton.addEventListener('click', () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });
});
