document.addEventListener("DOMContentLoaded", () => {
    const socket = io();
    const contentContainer = document.getElementById("content-container");

    const views = {
        main: `
            <div id="main-view">
                <div id="current-time">Время: </div>
                <div id="task-list-container">
                    <h2>Список задач</h2>
                    <ul id="task-list"></ul>
                </div>
                <div id="weather-container">
                    <h2>Погода на сегодня</h2>
                    <div id="today-weather"></div>
                    <h2>Погода на завтра</h2>
                    <div id="tomorrow-weather"></div>
                </div>
                <div id="birthdays-container">
                    <h2>Ближайшие дни рождения</h2>
                    <ul id="birthday-list"></ul>
                </div>
                <div id="holidays-container">
                    <h2>Ближайшие праздники</h2>
                    <ul id="holiday-list"></ul>
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
        birthdays: `
            <div id="birthdays-view">
                <h2>Дни рождения на 30 дней</h2>
                <ul id="birthday-list"></ul>
                <button id="back-to-main">Назад</button>
            </div>
        `,
        holidays: `
            <div id="holidays-view">
                <h2>Праздники на 30 дней</h2>
                <ul id="holiday-list"></ul>
                <button id="back-to-main">Назад</button>
            </div>
        `,
        tasksByDay: `
            <div id="tasks-by-day-view">
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

    socket.on('connect', () => {
        console.log("Socket connected");
        socket.emit('get_time');
    });

    socket.on("time_update", (data) => {
        const timeDiv = document.getElementById("current-time");
        if (timeDiv) timeDiv.textContent = `Время: ${data}`;
    });

    socket.on("new_task", (task) => {
        const taskList = document.getElementById("task-list");
        if (taskList) {
            const li = document.createElement("li");
            li.textContent = task;
            taskList.appendChild(li);
        }
    });

    window.handleTelegramCommand = function (command) {
        switch (command) {
            case "openWeatherDetails":
                renderView("weatherDetails");
                break;
            case "viewUpcomingBirthdays":
                renderView("birthdays");
                break;
            case "viewUpcomingHolidays":
                renderView("holidays");
                break;
            case "viewTasksByDay":
                renderView("tasksByDay");
                break;
            default:
                renderView("main");
        }
    };
});
