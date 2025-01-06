document.addEventListener("DOMContentLoaded", () => {
    const socket = io();
    const contentContainer = document.getElementById("content-container");

    let content_views = 'main';

    const views = {
        main: `
            <div id="main-view">
                <div class="d_container date_time_container">
                    <div class="left_date_time">
                        <div class="🤚">
                            <div class="👉"></div>
                            <div class="👉"></div>
                            <div class="👉"></div>
                            <div class="👉"></div>
                            <div class="🌴"></div>
                            <div class="👍"></div>
                        </div>
                    </div>
                    <div id="current-time" class="date_time">
                        <div id="time-text"></div>
                        <div id="day-text"></div>
                    </div>
                    <div class="right_date_time">
                        <div aria-label="Orange and tan hamster running in a metal wheel" role="img" class="wheel-and-hamster">
                            <div class="wheel"></div>
                            <div class="hamster">
                                <div class="hamster__body">
                                    <div class="hamster__head">
                                        <div class="hamster__ear"></div>
                                        <div class="hamster__eye"></div>
                                        <div class="hamster__nose"></div>
                                    </div>
                                    <div class="hamster__limb hamster__limb--fr"></div>
                                    <div class="hamster__limb hamster__limb--fl"></div>
                                    <div class="hamster__limb hamster__limb--br"></div>
                                    <div class="hamster__limb hamster__limb--bl"></div>
                                    <div class="hamster__tail"></div>
                                </div>
                            </div>
                            <div class="spoke"></div>
                        </div>
                    </div>
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
                            <div class="header_cont">Дни рождения</div>
                            <div id="birthday-list" class="list"></div>
                        </div>
                        <div id="holidays-container">
                            <div class="header_cont">Праздники</div>
                            <div id="holiday-list" class="list"></div>
                        </div>
                    </div>
                    <div id="tAndS">
                        <div id="task-list-container">
                            <div class="header_cont header_cont_bottom">Список задач</div>
                            <div id="task-list" class="list"></div>
                        </div>
                        <div id="shopp-list-container">
                            <div class="header_cont header_cont_bottom">Список покупок</div>
                            <div id="shopp-list" class="list"></div>
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
                <div id="hAndBDetails" class="d_container ">
                    <div id="birthdays-details-view">
                        <div class="header_cont_on_bAndH">Дни рождения</div>
                        <div id="birthday-list" class="list"></div>
                    </div>
                    <div id="holidays-details-view">
                        <div class="header_cont_on_bAndH">Праздники</div>
                        <div id="holiday-list" class="list"></div>
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
        if (content_views === 'main') {
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
                        <div class="inscription_we inscription_temp">${entry.temp}°C</div>
                    `;
                    chart.appendChild(item);
                });
            }
        }
    });

    socket.on('birthdays_update', (data) => {
        if (content_views === 'main') {
            const birthdaysList = document.getElementById("birthday-list");
            birthdaysList.style.height = '70%';
            birthdaysList.innerHTML = '';
            if (data.length > 0) {
                data.forEach(birthday => {
                    const div = document.createElement("div");
                    if (birthday.flag_today === 1) {
                        div.className = 'animation_bounce'
                    }
                    div.textContent = `${birthday.name} - ${birthday.date}`;
                    birthdaysList.appendChild(div);
                });
            } else {
                const div = document.createElement("div");
                div.textContent = 'В ближайшие 30 дней нет';
                birthdaysList.appendChild(div);
            }
            updateVisibleItems()
        }
    });

    socket.on('holidays_update', (data) => {
        if (content_views === 'main') {
            const holidaysList = document.getElementById("holiday-list");
            holidaysList.style.height = '70%';
            holidaysList.innerHTML = '';
            if (data.length > 0) {
                data.forEach(holiday => {
                    const div = document.createElement("div");
                    if (holiday.flag_today === 1) {
                        div.className = 'animation_bounce'
                    }
                    div.textContent = `${holiday.name} - ${holiday.date}`;
                    holidaysList.appendChild(div);
                });
            } else {
                const div = document.createElement("div");
                div.textContent = 'В ближайшие 30 дней нет';
                holidaysList.appendChild(div);
            }
            updateVisibleItems()
        }
    });

    socket.on('todo_update', (data) => {
        if (content_views === 'main') {
            const taskList = document.getElementById("task-list");
            taskList.innerHTML = '';
            if (data.length > 0) {
                data.forEach(task => {
                    const div = document.createElement("div");
                    if (task.flag_today === 1) {
                        div.className = 'animation_bounce'
                    }
                    div.id = `task_${task.id}`;
                    if (task.deadline) {
                        div.textContent = `${task.task} до ${task.deadline}`;
                    } else {
                        div.textContent = `${task.task}`;
                    }
                    taskList.appendChild(div);
                });
            } else {
                const div = document.createElement("div");
                div.id = `empty_task`;
                div.textContent = 'Нет невыполненных задач';
                taskList.appendChild(div);
            }
            updateVisibleItems()
        }
    });

    socket.on('shopp_list_update', (data) => {
        if (content_views === 'main') {
            const shoppList = document.getElementById("shopp-list");
            shoppList.innerHTML = '';
            if (data.length > 0) {
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
            } else {
                const div = document.createElement("div");
                div.id = `empty_shoppList`;
                div.textContent = 'Нет покупок';
                shoppList.appendChild(div);
            }
            updateVisibleItems()

        }
    });

    function updateVisibleItems() {
        const containerConfigs = [
            { id: 'shopp-list', showExclamation: true },
            { id: 'task-list', showExclamation: true },
            { id: 'holiday-list', showExclamation: false },
            { id: 'birthday-list', showExclamation: false }
        ];

        for (const { id, showExclamation } of containerConfigs) {
            const container = document.getElementById(id);
            if (!container) continue;

            const items = container.children;
            const containerRect = container.getBoundingClientRect();
            let hasOverflow = false;

            for (const item of items) {
                const itemRect = item.getBoundingClientRect();
                if (itemRect.bottom > containerRect.bottom) {
                    item.style.display = 'none';
                    hasOverflow = true;
                } else {
                    item.style.display = '';
                }
            }

            if (showExclamation) {
                let exclamationMark = container.querySelector('.exclamation-mark');
                if (!exclamationMark) {
                    exclamationMark = document.createElement('div');
                    exclamationMark.className = 'exclamation-mark';
                    exclamationMark.textContent = '!';
                    container.appendChild(exclamationMark);
                }
                exclamationMark.style.display = hasOverflow ? 'block' : 'none';
            }
        }
    }

    // Добавление новых данных
    socket.on("new_task", (task) => {
        if (content_views === 'main') {
            const taskList = document.getElementById("task-list");
            if (taskList) {
                const emptyTask = taskList.querySelector("#empty_task");
                if (emptyTask) {
                    taskList.removeChild(emptyTask);
                }
                const div = document.createElement("div");
                if (task.flag_today === 1) {
                    div.className = 'animation_bounce'
                }
                div.id = `task_${task.id}`;
                if (task.deadline) {
                    div.textContent = `${task.task} до ${task.deadline}`;
                } else {
                    div.textContent = `${task.task}`;
                }
                taskList.appendChild(div);
            }
            updateVisibleItems()
        }
    });

    socket.on("delete_task", (data) => {
        if (content_views === 'main') {
            const task_id = data.task_id;
            const taskElement = document.getElementById(`task_${task_id}`);
            if (taskElement) {
                taskElement.remove();
            }
            const taskList = document.getElementById("task-list");
            if (taskList.children.length === 0) {
                const div = document.createElement("div");
                div.id = `empty_task`;
                div.textContent = 'Нет невыполненных дел';
                taskList.appendChild(div);
            }
        }
    });

    socket.on("new_purchase", (purchase) => {
        if (content_views === 'main') {
            const shoppList = document.getElementById("shopp-list");
            if (shoppList) {
                const emptyShoppList = shoppList.querySelector("#empty_shoppList");
                if (emptyShoppList) {
                    shoppList.removeChild(emptyShoppList);
                }
                const div = document.createElement("div");
                div.id = `purchase_${purchase.id}`;
                if (purchase.size) {
                    div.textContent = `"${purchase.name}" ${purchase.size} в количестве ${purchase.quantity} шт.`;
                } else {
                    div.textContent = `"${purchase.name}" в количестве ${purchase.quantity} шт.`;
                }
                shoppList.appendChild(div);
            }
            updateVisibleItems()
        }
    });

    socket.on("delete_purchase", (data) => {
        if (content_views === 'main') {
            const purchase_id = data.purchase_id;
            const purchaseElement = document.getElementById(`purchase_${purchase_id}`);
            if (purchaseElement) {
                purchaseElement.remove();
            }
            const shoppList = document.getElementById("shopp-list");
            if (shoppList.children.length === 0) {
                const div = document.createElement("div");
                div.id = `empty_shoppList`;
                div.textContent = 'Нет покупок';
                shoppList.appendChild(div);
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
        holidaysList.style.height = '88%';
        holidaysList.innerHTML = '';
        data.holidays.forEach(holiday => {
            const div = document.createElement("div");
            if (holiday.flag_today === 1) {
                    div.className = 'animation_bounce'
                }
            div.textContent = `${holiday.name} - ${holiday.date}`;
            holidaysList.appendChild(div);
        });
        const birthdaysList = document.getElementById("birthday-list");
        birthdaysList.style.height = '88%';
        birthdaysList.innerHTML = '';
        data.birthdays.forEach(birthday => {
            const div = document.createElement("div");
            if (birthday.flag_today === 1) {
                    div.className = 'animation_bounce'
                }
            div.textContent = `${birthday.name} - ${birthday.date}`;
            birthdaysList.appendChild(div);
        });
        updateVisibleItems()
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
