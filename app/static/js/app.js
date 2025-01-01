document.addEventListener("DOMContentLoaded", () => {
    const socket = io();
    const contentContainer = document.getElementById("content-container");

    const views = {
        main: `
            <div id="main-view">
                <div id="current-time">Время: </div>
                <div id="weather-container">
                    <div class="weather-upper">
                        <h2 id="current-temp">- °C</h2>
                        <img id="current-icon" src="" alt="Погода">
                        <p id="current-desc">---</p>
                        <p>Ветер: <span id="current-wind">-</span> м/с</p>
                        <p>Влажность: <span id="current-humidity">-</span>%</p>
                    </div>
                    <div class="weather-lower">
                        <div class="weather-chart" id="weather-chart"></div>
                    </div>
                </div>
                <div id="birthdays-container">
                    <h2>Ближайшие дни рождения</h2>
                    <ul id="birthday-list"></ul>
                </div>
                <div id="holidays-container">
                    <h2>Ближайшие праздники</h2>
                    <ul id="holiday-list"></ul>
                </div>
                <div id="task-list-container">
                    <h2>Список задач</h2>
                    <ul id="task-list"></ul>
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
    });

    // Полное обновление контейнеров
    socket.on("time_update", (data) => {
        const timeDiv = document.getElementById("current-time");
        if (timeDiv) timeDiv.textContent = `Время: ${data}`;
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
                item.innerHTML = `
                    <div>${entry.time}</div>
                    <img src="${entry.icon}" alt="${entry.description}">
                    <div>${entry.temp}°C</div>
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
            const li = document.createElement("li");
            li.id = `task_${task.id}`;
            li.textContent = `Время: ${task.time} - Задача: ${task.task}`;
            taskList.appendChild(li);
        });
    });

    // Добавление новых данных
    socket.on("new_task", (task) => {
        const taskList = document.getElementById("task-list");
        if (taskList) {
            const li = document.createElement("li");
            li.id = `task_${task.id}`;
            li.textContent = `Время: ${task.time} - Задача: ${task.task}`;
            taskList.appendChild(li);
        }
    });

    socket.on("delete_task", (data) => {
        console.log(data)
        const task_id = data.task_id;
        const taskElement = document.getElementById(`task_${task_id}`);
        if (taskElement) {
            taskElement.remove();
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
