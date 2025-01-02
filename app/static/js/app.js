document.addEventListener("DOMContentLoaded", () => {
    const socket = io();
    const contentContainer = document.getElementById("content-container");

    let content_views = 'main';

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
            <div id="main-view">
                <div id="current-time" class="d_container">
                    <div id="time-text"></div>
                    <div id="day-text"></div>
                </div>
                <div id="weather-details-view">
                    <div id="detailed-weather" class="weather-row"></div>
                </div>
            </div>
        `,
        birthdaysAndHolidaysDetails: `
            <div id="main-view">
                <div id="current-time" class="d_container">
                    <div id="time-text"></div>
                    <div id="day-text"></div>
                </div>
                <div id="hAndBDetails" class="d_container">
                    <div id="birthdays-details-view">
                        <div>Дни рождения</div>
                        <ul id="birthday-list"></ul>
                    </div>
                    <div id="holidays-details-view">
                        <div>Праздники</div>
                        <ul id="holiday-list"></ul>
                    </div>
                </div>
            </div>
        `,
    };

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
            const div = document.createElement("div");
            div.textContent = `${birthday.name} - ${birthday.date}`;
            birthdaysList.appendChild(div);
        });
    });

    socket.on('holidays_update', (data) => {
        const holidaysList = document.getElementById("holiday-list");
        holidaysList.innerHTML = '';
        data.forEach(holiday => {
            const div = document.createElement("div");
            div.textContent = `${holiday.name} - ${holiday.date}`;
            holidaysList.appendChild(div);
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
        if (content_views === 'main') {
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
        }
    });

    socket.on("delete_task", (data) => {
        if (content_views === 'main') {
            const task_id = data.task_id;
            const taskElement = document.getElementById(`task_${task_id}`);
            if (taskElement) {
                taskElement.remove();
            }
        }
    });

    socket.on("new_purchase", (purchase) => {
        if (content_views === 'main') {
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
        }
    });

    socket.on("delete_purchase", (data) => {
        if (content_views === 'main') {
            const purchase_id = data.purchase_id;
            const purchaseElement = document.getElementById(`purchase_${purchase_id}`);
            if (purchaseElement) {
                purchaseElement.remove();
            }
        }
    });

    // Переключение страниц
    function renderView(view) {
        contentContainer.innerHTML = views[view];
        if (view === 'main') {
            socket.emit('get_time');
            socket.emit('get_weather');
            socket.emit('get_birthdays');
            socket.emit('get_holidays');
            socket.emit('get_todo');
            socket.emit('get_shopp_list');
        } else if (view === 'weatherDetails') {
            socket.emit('get_time');
            socket.emit('get_weather_details');
        } else if (view === 'birthdaysAndHolidaysDetails') {
            socket.emit('get_time');
            socket.emit('get_bAndH_details');
        }
    }

    renderView(content_views);

    socket.on('manageScr', (data) => {
        handleTelegramCommand(data.command)
    });

    socket.on('holidays_and_birthdays_details_update', (data) => {
        const holidaysList = document.getElementById("holiday-list");
        holidaysList.innerHTML = '';
        data.holidays.forEach(holiday => {
            const div = document.createElement("div");
            div.textContent = `${holiday.name} - ${holiday.date}`;
            holidaysList.appendChild(div);
        });
        const birthdaysList = document.getElementById("birthday-list");
        birthdaysList.innerHTML = '';
        data.birthdays.forEach(birthday => {
            const div = document.createElement("div");
            div.textContent = `${birthday.name} - ${birthday.date}`;
            birthdaysList.appendChild(div);
        });
    });

    socket.on('weather_details_update', (data) => {
        const detailedWeatherContainer = document.getElementById('detailed-weather');
        detailedWeatherContainer.innerHTML = '';

        data.hourly.forEach(dayData => {
            const dayContainer = document.createElement('div');
            dayContainer.classList.add('weather-day');

            const dayTitle = document.createElement('h3');
            dayTitle.textContent = dayData.day;
            dayContainer.appendChild(dayTitle);

            dayData.entries.forEach(forecast => {
                const card = document.createElement('div');
                card.classList.add('weather-card');
                card.innerHTML = `
                    <div>${forecast.time}</div>
                    <img src="${forecast.icon}" alt="${forecast.description}" class="weather-icon">
                    <div>${forecast.temp}°C</div>
                    <div>${forecast.description}</div>
                    <div>Ветер: ${forecast.wind_speed} м/с</div>
                    <div>Влажность: ${forecast.humidity}%</div>
                `;
                dayContainer.appendChild(card);
            });

            detailedWeatherContainer.appendChild(dayContainer);
        });
    });


    window.handleTelegramCommand = function (command) {
        switch (command) {
            case "openWeatherDetails":
                content_views = 'weatherDetails';
                renderView(content_views);
                break;
            case "openBirthdaysAndHolidaysDetails":
                content_views = 'birthdaysAndHolidaysDetails';
                renderView(content_views);
                break;
            default:
                content_views = 'main';
                renderView(content_views);
        }
    };
});
