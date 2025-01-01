document.addEventListener("DOMContentLoaded", () => {
    const socket = io();
    const contentContainer = document.getElementById("content-container");

    const views = {
        main: `
            <div id="main-view">
                <div id="current-time" class="d_container">
                    <div id="time-text"></div>
                    <div id="day-text"></div>
                </div>
                <div id="weather-container" class="d_container">
                    <div class="weather-upper">
                        <div id="current-temp">- °C</div>
                        <img id="current-icon" src="" alt="Погода">
                        <div id="current-desc">---</div>
                        <div>Ветер: <span id="current-wind">-</span> м/с</div>
                        <div>Влажность: <span id="current-humidity">-</span>%</div>
                    </div>
                    <div class="weather-lower">
                        <div class="weather-chart" id="weather-chart"></div>
                    </div>
                </div>
                <div id="reminder-container" class="d_container">
                    <div id="bAndH">
                        <div id="birthdays-container">
                            <div>Дни рождения</div>
                            <ul id="birthday-list"></ul>
                        </div>
                        <div id="holidays-container">
                            <div>Праздники</div>
                            <ul id="holiday-list"></ul>
                        </div>
                    </div>
                    <div id="tAndS">
                        <div id="task-list-container">
                            <div>Список задач</div>
                            <ul id="task-list"></ul>
                        </div>
                        <div id="shopp-list-container">
                            <div>Список покупок</div>
                            <ul id="shopp-list"></ul>
                        </div>
                    </div>
                </div>
            </div>
        `,
        weatherDetails: `
            <div id="weather-details-view">
                <h2>Детальный прогноз погоды</h2>
                <div id="detailed-weather"></div>
                <button id="back-to-main">Назад</button>
            </div>
        `,
        birthdaysDetails: `
            <div id="birthdays-details-view">
                <h2>Дни рождения на 30 дней</h2>
                <ul id="birthday-list"></ul>
                <button id="back-to-main">Назад</button>
            </div>
        `,
        holidaysDetails: `
            <div id="holidays-details-view">
                <h2>Праздники на 30 дней</h2>
                <ul id="holiday-list"></ul>
                <button id="back-to-main">Назад</button>
            </div>
        `,
        tasksDetails: `
            <div id="tasks-details-view">
                <h2>Список задач по дням</h2>
                <div id="tasks-grouped"></div>
                <button id="back-to-main">Назад</button>
            </div>
        `,
    };

    function renderView(view) {
        contentContainer.innerHTML = views[view];
    }

    renderView("main");

    // Первичное получение данных
    socket.on('connect', () => {
        socket.emit('get_time');
        socket.emit('get_weather');
        socket.emit('get_birthdays');
        socket.emit('get_holidays');
        socket.emit('get_todo');
        socket.emit('get_shopp_list');
    });

    // Полное обновление контейнеров
    socket.on("time_update", (data) => {
        const timeDiv = document.getElementById("time-text");
        const dayDiv = document.getElementById("day-text");
        if (data) {
            timeDiv.textContent = `${data.current_time}`;
            dayDiv.textContent = `${data.formatted_date}`;
        }
    });

    socket.on("weather_update", (data) => {
        if (data.current) {
            document.getElementById("current-temp").textContent = `${data.current.temp}°C`;
            document.getElementById("current-icon").src = data.current.icon;
            document.getElementById("current-desc").textContent = data.current.description;
            document.getElementById("current-wind").textContent = data.current.wind_speed;
            document.getElementById("current-humidity").textContent = data.current.humidity;
        }

        if (data.hourly) {
            const chart = document.getElementById("weather-chart");
            chart.innerHTML = '';

            data.hourly.forEach(entry => {
                const item = document.createElement("div");
                item.className = 'weather_hour_card';
                item.innerHTML = `
                    <div class="inscription_we">${entry.time}</div>
                    <img src="${entry.icon}" alt="${entry.description}">
                    <div class="inscription_we">${entry.temp}°C</div>
                `;
                chart.appendChild(item);
            });
        }
    });

    socket.on('birthdays_update', (data) => {
        const birthdaysList = document.getElementById("birthday-list");
        birthdaysList.innerHTML = '';
        data.forEach(birthday => {
            const li = document.createElement("li");
            li.textContent = `Дата: ${birthday.date} - Название праздника: ${birthday.name}`;
            birthdaysList.appendChild(li);
        });
    });

    socket.on('holidays_update', (data) => {
        const holidaysList = document.getElementById("holiday-list");
        holidaysList.innerHTML = '';
        data.forEach(holiday => {
            const li = document.createElement("li");
            li.textContent = `Дата: ${holiday.date} - Название праздника: ${holiday.name}`;
            holidaysList.appendChild(li);
        });
    });

    socket.on('todo_update', (data) => {
        const taskList = document.getElementById("task-list");
        taskList.innerHTML = '';
        data.forEach(task => {
            const div = document.createElement("div");
            div.id = `task_${task.id}`;
            if (task.deadline) {
                div.textContent = `${task.task} до ${task.deadline}`;
            } else {
                div.textContent = `${task.task}`;
            }
            taskList.appendChild(div);
        });
    });

    socket.on('shopp_list_update', (data) => {
        const shoppList = document.getElementById("shopp-list");
        shoppList.innerHTML = '';
        data.forEach(purchase => {
            const div = document.createElement("div");
            div.id = `purchase_${purchase.id}`;
            if (purchase.size) {
                div.textContent = `"${purchase.name}" ${purchase.size} в количестве ${purchase.quantity} шт.`;
            } else {
                div.textContent = `"${purchase.name}" в количестве ${purchase.quantity} шт.`;
            }
            shoppList.appendChild(div);
        });
    });

    // Добавление новых данных
    socket.on("new_task", (task) => {
        const taskList = document.getElementById("task-list");
        if (taskList) {
            const div = document.createElement("div");
            div.id = `task_${task.id}`;
            if (task.deadline) {
                div.textContent = `${task.task} до ${task.deadline}`;
            } else {
                div.textContent = `${task.task}`;
            }
            taskList.appendChild(div);
        }
    });

    socket.on("delete_task", (data) => {
        const task_id = data.task_id;
        const taskElement = document.getElementById(`task_${task_id}`);
        if (taskElement) {
            taskElement.remove();
        }
    });

    socket.on("new_purchase", (purchase) => {
        const shoppList = document.getElementById("shopp-list");
        if (shoppList) {
            const div = document.createElement("div");
            div.id = `purchase_${purchase.id}`;
            if (purchase.size) {
                div.textContent = `"${purchase.name}" ${purchase.size} в количестве ${purchase.quantity} шт.`;
            } else {
                div.textContent = `"${purchase.name}" в количестве ${purchase.quantity} шт.`;
            }
            shoppList.appendChild(div);
        }
    });

    socket.on("delete_purchase", (data) => {
        const purchase_id = data.purchase_id;
        const purchaseElement = document.getElementById(`purchase_${task_id}`);
        if (purchaseElement) {
            purchaseElement.remove();
        }
    });

    window.handleTelegramCommand = function (command) {
        switch (command) {
            case "openWeatherDetails":
                renderView("weatherDetails");
                break;
            case "openBirthdaysDetails":
                renderView("birthdaysDetails");
                break;
            case "openHolidaysDetails":
                renderView("holidaysDetails");
                break;
            case "opemTasksDetails":
                renderView("tasksDetails");
                break;
            default:
                renderView("main");
        }
    };
});
