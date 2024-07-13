document.addEventListener('DOMContentLoaded', (event) => {
    const prevWeekBtn = document.getElementById('prevWeek');
    const nextWeekBtn = document.getElementById('nextWeek');
    const totalHoursElement = document.getElementById('totalHours');
    const addScheduleBtn = document.getElementById('addSchedule');
    let currentWeek = new Date();

    // 初始化從 LocalStorage 獲取的排程
    let schedule = JSON.parse(localStorage.getItem('schedule')) || {
        "7/16": { start: "16:00", end: "22:00" },
        "7/18": { start: "16:00", end: "22:00" },
        "7/20": { start: "14:30", end: "22:00" },
        "7/22": { start: "10:30", end: "16:30" },
        "7/23": { start: "10:30", end: "16:30" },    
        "7/24": { start: "14:30", end: "20:30" }
    };
    
    function updateWeek(direction) {
        currentWeek.setDate(currentWeek.getDate() + direction * 7);
        updateDates();
        updateSchedule();
        updateTotalHours();
    }
    
    function updateDates() {
        const dayHeaders = document.querySelectorAll('.day-header');
        for (let i = 0; i < 7; i++) {
            const date = new Date(currentWeek);
            date.setDate(date.getDate() - date.getDay() + i + 1);
            dayHeaders[i].innerHTML = `${['一','二','三','四','五','六','日'][i]}<br>${date.getMonth() + 1}/${date.getDate()}`;
        }
    }
    
    function updateSchedule() {
        const dayContents = document.querySelectorAll('.day-content');
        dayContents.forEach(content => content.innerHTML = ''); // 清空原有內容
    
        dayContents.forEach((content, index) => {
            const header = content.parentElement.querySelector('.day-header').innerText.split('<br>')[1];
            if (schedule[header]) {
                const { start, end } = schedule[header];
                const startTime = parseTime(start);
                const endTime = parseTime(end);
                const duration = (endTime - startTime) / 3600000; // 轉換為小時
                const topPosition = ((startTime.getHours() - 7) * 60 + startTime.getMinutes()) / (17 * 60) * 100; // 假設早上7點開始
                const height = (duration * 60) / (17 * 60) * 100; // 17小時的一天
    
                const scheduleItem = document.createElement('div');
                scheduleItem.classList.add('schedule-item');
                scheduleItem.style.top = `${topPosition}%`;
                scheduleItem.style.height = `${height}%`;
                scheduleItem.innerHTML = `🐰<br>${start}<br><span class="vertical-line"></span><br>${end}`;
    
                content.appendChild(scheduleItem);
            }
        });
    }
    
    function updateTotalHours() {
        let totalHours = 0;
        const scheduleItems = document.querySelectorAll('.schedule-item');
        scheduleItems.forEach(item => {
            const start = parseTime(item.innerText.split('\n')[1]);
            const end = parseTime(item.innerText.split('\n')[3]);
            totalHours += (end - start) / 3600000; // 轉換為小時
        });
        totalHoursElement.textContent = `本週總工時：${totalHours.toFixed(1)}小時`;
    }
    
    function parseTime(timeStr) {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return new Date(0, 0, 0, hours, minutes);
    }
    
    function addSchedule() {
        const dateInput = document.getElementById('date').value;
        const startInput = document.getElementById('start').value;
        const endInput = document.getElementById('end').value;
    
        if (dateInput && startInput && endInput) {
            schedule[dateInput] = { start: startInput, end: endInput };
            localStorage.setItem('schedule', JSON.stringify(schedule));
            updateSchedule();
            updateTotalHours();
        }
    }
    
    addScheduleBtn.addEventListener('click', addSchedule);
    prevWeekBtn.addEventListener('click', () => updateWeek(-1));
    nextWeekBtn.addEventListener('click', () => updateWeek(1));
    
    updateDates();
    updateSchedule();
    updateTotalHours();});