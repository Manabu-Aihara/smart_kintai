// select要素の変更をhidden inputに同期
document.addEventListener('DOMContentLoaded', function () {
  // 申請AMの同期
  document.querySelectorAll('.notification-select').forEach(function (select) {
    const index = select.getAttribute('data-index');
    const hiddenInput = document.getElementById('notifications_' + index);

    // 初期値の設定
    if (hiddenInput) {
      hiddenInput.value = select.value;
    }

    // 変更時の同期
    select.addEventListener('change', function () {
      if (hiddenInput) {
        hiddenInput.value = this.value;
      }
    });
  });

  // 申請PMの同期
  document.querySelectorAll('.notification-pm-select').forEach(function (select) {
    const index = select.getAttribute('data-index');
    const hiddenInput = document.getElementById('notifications_pm_' + index);

    // 初期値の設定
    if (hiddenInput) {
      hiddenInput.value = select.value;
    }

    // 変更時の同期
    select.addEventListener('change', function () {
      if (hiddenInput) {
        hiddenInput.value = this.value;
      }
      console.log(`hiddenInput: ${hiddenInput}`);
    });
    console.log(`select.value: ${select.value}`);
  });
});
