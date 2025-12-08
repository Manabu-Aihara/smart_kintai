const remainingHolidays = document.getElementById('holiday-remain').value;
// if (remainingHolidays && parseInt(remainingHolidays) > 0) {
//     alert(`今月末で、${remainingHolidays}日分の有給休暇が消えてしまいます。`);
// }
const notifications = document.querySelectorAll('.notifications');
const notifications_pm = document.querySelectorAll('.notifications_pm');
const notificationArr = [];
const notificationHalfArr = [];
const notificationTimeRestArr = ["10", "11", "12", "13", "14", "15"];
let timeRestFlag = false;

const alertMonth = document.getElementById('alert-month').value;
if (alertMonth === '3' || alertMonth === '9') {
    notifications.forEach((notification) => {
        if (notification.textContent == '3' || notification.textContent == '9') {
            notificationArr.push(notification.textContent);
        } else if (notification.textContent == '4') {
            notificationHalfArr.push(notification.textContent);
        }
        if (notificationTimeRestArr.includes(notification.textContent)) {
            timeRestFlag = true;
        }
    });
    notifications_pm.forEach((notification_pm) => {
        if (notification_pm.textContent == '4' || notification_pm.textContent == '9') {
            notificationHalfArr.push(notification_pm.textContent);
        }
        if (notificationTimeRestArr.includes(notification_pm.textContent)) {
            timeRestFlag = true;
        }
    });
    displayRemains = parseFloat(remainingHolidays) - ((notificationArr.length * 1) + (notificationHalfArr.length * 0.5));
}
console.log(timeRestFlag);

const alertRemain = document.getElementById('alert-remain');
alertRemain.textContent = displayRemains;
const alertTime = document.getElementById('alert-time');
if (timeRestFlag) {
    alertTime.textContent = ' - 時間休分(1〜)';
} else {
    alertTime.textContent = '';
}
