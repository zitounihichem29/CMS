/* =========================================================
   ORSC — CLUB MANAGEMENT SYSTEM
   JAVASCRIPT
   ========================================================= */


/* =========================================================
   1. DOM READY
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    initNavigation();

    initDarkMode();

    initMobileMenu();

    initLoginModal();

    initTasks();

    initFilters();

    initQuickActions();

    initNotifications();

    initCalendar();

    initProfile();

    initButtons();

});


/* =========================================================
   2. PAGE NAVIGATION
   ========================================================= */

function initNavigation() {

    const navItems = document.querySelectorAll(
        ".nav-item, .bottom-nav button[data-page]"
    );

    const pages = document.querySelectorAll(".page");


    navItems.forEach(item => {

        item.addEventListener("click", () => {

            const targetPage =
                item.dataset.page ||
                item.getAttribute("data-page");

            if (!targetPage) return;

            showPage(targetPage);

        });

    });


    function showPage(pageId) {

        pages.forEach(page => {

            page.classList.remove("active");

        });


        const target = document.getElementById(pageId);

        if (target) {

            target.classList.add("active");

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });

        }


        navItems.forEach(item => {

            item.classList.remove("active");

            if (
                item.dataset.page === pageId ||
                item.getAttribute("data-page") === pageId
            ) {

                item.classList.add("active");

            }

        });


        // Close mobile sidebar after navigation

        const sidebar =
            document.querySelector(".sidebar");

        if (sidebar) {

            sidebar.classList.remove("open");

        }

    }


    // Make it available globally

    window.showPage = showPage;

}


/* =========================================================
   3. DARK / LIGHT MODE
   ========================================================= */

function initDarkMode() {

    const themeButtons = document.querySelectorAll(
        "[data-theme], #themeToggle, .theme-toggle"
    );


    // Restore saved theme

    const savedTheme =
        localStorage.getItem("orsc-theme");


    if (savedTheme === "dark") {

        document.body.classList.add("dark");

    }


    if (savedTheme === "light") {

        document.body.classList.remove("dark");

    }


    themeButtons.forEach(button => {

        button.addEventListener("click", toggleTheme);

    });


    updateThemeIcons();


    function toggleTheme() {

        document.body.classList.toggle("dark");

        const isDark =
            document.body.classList.contains("dark");


        localStorage.setItem(
            "orsc-theme",
            isDark ? "dark" : "light"
        );


        updateThemeIcons();

        showToast(
            isDark
                ? "Dark mode activated"
                : "Light mode activated"
        );

    }


    function updateThemeIcons() {

        const isDark =
            document.body.classList.contains("dark");


        document.querySelectorAll(
            "[data-theme-icon], .theme-icon"
        ).forEach(icon => {

            icon.textContent =
                isDark ? "☀" : "☾";

        });

    }


    window.toggleTheme = toggleTheme;

}


/* =========================================================
   4. MOBILE SIDEBAR
   ========================================================= */

function initMobileMenu() {

    const menuButton =
        document.querySelector(
            ".mobile-menu, #mobileMenu"
        );


    const sidebar =
        document.querySelector(".sidebar");


    if (!menuButton || !sidebar) return;


    menuButton.addEventListener("click", () => {

        sidebar.classList.toggle("open");

    });


    // Close when clicking outside

    document.addEventListener("click", event => {

        if (
            window.innerWidth <= 760 &&
            sidebar.classList.contains("open") &&
            !sidebar.contains(event.target) &&
            !menuButton.contains(event.target)
        ) {

            sidebar.classList.remove("open");

        }

    });

}


/* =========================================================
   5. LOGIN MODAL
   ========================================================= */

function initLoginModal() {

    const modal =
        document.querySelector(
            ".login-modal, #loginModal"
        );


    if (!modal) return;


    const openButtons =
        document.querySelectorAll(
            "[data-login], #loginButton, .login-button"
        );


    const closeButtons =
        modal.querySelectorAll(
            ".modal-close, [data-close]"
        );


    openButtons.forEach(button => {

        button.addEventListener("click", () => {

            openLogin();

        });

    });


    closeButtons.forEach(button => {

        button.addEventListener("click", () => {

            closeLogin();

        });

    });


    modal.addEventListener("click", event => {

        if (event.target === modal) {

            closeLogin();

        }

    });


    document.addEventListener("keydown", event => {

        if (
            event.key === "Escape" &&
            modal.classList.contains("open")
        ) {

            closeLogin();

        }

    });


    function openLogin() {

        modal.classList.add("open");

        document.body.style.overflow = "hidden";

        const firstInput =
            modal.querySelector("input");

        if (firstInput) {

            setTimeout(() => {

                firstInput.focus();

            }, 200);

        }

    }


    function closeLogin() {

        modal.classList.remove("open");

        document.body.style.overflow = "";

    }


    window.openLogin = openLogin;

    window.closeLogin = closeLogin;

}


/* =========================================================
   6. LOGIN FORM
   ========================================================= */

document.addEventListener("submit", event => {

    const form =
        event.target.closest(
            ".login-panel form, #loginForm"
        );


    if (!form) return;


    event.preventDefault();


    const email =
        form.querySelector(
            'input[type="email"], input[name="email"]'
        );


    const password =
        form.querySelector(
            'input[type="password"], input[name="password"]'
        );


    if (!email || !password) {

        showToast("Please complete the form");

        return;

    }


    if (!email.value.trim()) {

        showToast("Please enter your email");

        email.focus();

        return;

    }


    if (!password.value.trim()) {

        showToast("Please enter your password");

        password.focus();

        return;

    }


    /*
     * FRONT-END DEMO ONLY
     *
     * The real authentication will later be
     * connected to the CMS backend/database.
     */

    showToast("Login request sent");


    setTimeout(() => {

        closeLoginIfAvailable();

    }, 800);

});


function closeLoginIfAvailable() {

    const modal =
        document.querySelector(
            ".login-modal, #loginModal"
        );


    if (modal) {

        modal.classList.remove("open");

        document.body.style.overflow = "";

    }

}


/* =========================================================
   7. TASK MANAGEMENT
   ========================================================= */

function initTasks() {

    const taskButtons =
        document.querySelectorAll(
            ".task-check, .full-task-check, [data-task-check]"
        );


    taskButtons.forEach(button => {

        button.addEventListener("click", () => {

            const task =
                button.closest(
                    ".task-row, .full-task"
                );


            if (!task) return;


            const completed =
                task.classList.toggle("completed");


            if (completed) {

                button.innerHTML = "✓";

                button.style.opacity = "0.65";


                const text =
                    task.querySelector(
                        "b, strong"
                    );


                if (text) {

                    text.style.textDecoration =
                        "line-through";

                    text.style.opacity =
                        "0.55";

                }


                showToast("Task completed");

            } else {

                button.innerHTML = "";

                button.style.opacity = "1";


                const text =
                    task.querySelector(
                        "b, strong"
                    );


                if (text) {

                    text.style.textDecoration =
                        "none";

                    text.style.opacity =
                        "1";

                }


                showToast("Task reopened");

            }


            updateTaskProgress();

        });

    });


    function updateTaskProgress() {

        const tasks =
            document.querySelectorAll(
                ".full-task"
            );


        if (!tasks.length) return;


        const completed =
            document.querySelectorAll(
                ".full-task.completed"
            ).length;


        const percentage =
            Math.round(
                (completed / tasks.length) * 100
            );


        const progressBars =
            document.querySelectorAll(
                ".progress i"
            );


        progressBars.forEach(bar => {

            bar.style.width =
                `${percentage}%`;

        });


        const progressNumbers =
            document.querySelectorAll(
                "[data-progress]"
            );


        progressNumbers.forEach(number => {

            number.textContent =
                `${percentage}%`;

        });

    }

}


/* =========================================================
   8. TASK FILTERS
   ========================================================= */

function initFilters() {

    const filterGroups =
        document.querySelectorAll(
            ".task-filters, .filter-pills"
        );


    filterGroups.forEach(group => {

        const buttons =
            group.querySelectorAll("button");


        buttons.forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    buttons.forEach(btn => {

                        btn.classList.remove(
                            "active"
                        );

                    });


                    button.classList.add(
                        "active"
                    );


                    const filter =
                        button.dataset.filter ||
                        button.textContent
                            .trim()
                            .toLowerCase();


                    applyFilter(
                        filter,
                        group
                    );

                }
            );

        });

    });


    function applyFilter(filter, group) {

        // TASK FILTERS

        if (
            group.classList.contains(
                "task-filters"
            )
        ) {

            const tasks =
                document.querySelectorAll(
                    ".full-task"
                );


            tasks.forEach(task => {

                const isCompleted =
                    task.classList.contains(
                        "completed"
                    );


                if (
                    filter === "all" ||
                    filter === "toutes" ||
                    filter === "all tasks"
                ) {

                    task.style.display = "";

                }

                else if (
                    filter.includes("done") ||
                    filter.includes("completed") ||
                    filter.includes("termin")
                ) {

                    task.style.display =
                        isCompleted
                            ? "flex"
                            : "none";

                }

                else if (
                    filter.includes("pending") ||
                    filter.includes("todo") ||
                    filter.includes("à faire")
                ) {

                    task.style.display =
                        !isCompleted
                            ? "flex"
                            : "none";

                }

            });

        }


        // EVENT FILTERS

        if (
            group.classList.contains(
                "filter-pills"
            )
        ) {

            const events =
                document.querySelectorAll(
                    ".event-card"
                );


            events.forEach(eventCard => {

                if (
                    filter === "all" ||
                    filter === "all events" ||
                    filter === "tous"
                ) {

                    eventCard.style.display = "";

                }

                else {

                    const category =
                        (
                            eventCard.dataset.category ||
                            ""
                        ).toLowerCase();


                    eventCard.style.display =
                        category.includes(filter)
                            ? ""
                            : "none";

                }

            });

        }

    }

}


/* =========================================================
   9. QUICK ACTIONS
   ========================================================= */

function initQuickActions() {

    const buttons =
        document.querySelectorAll(
            ".quick-grid button, .member-shortcuts button"
        );


    buttons.forEach(button => {

        button.addEventListener("click", () => {

            const page =
                button.dataset.page;


            if (page) {

                if (
                    typeof window.showPage ===
                    "function"
                ) {

                    window.showPage(page);

                }

                return;

            }


            const action =
                button.dataset.action ||
                button.querySelector("span")?.textContent ||
                "Action";


            showToast(
                `${action} selected`
            );

        });

    });

}


/* =========================================================
   10. NOTIFICATIONS
   ========================================================= */

function initNotifications() {

    const notificationButtons =
        document.querySelectorAll(
            ".notification-btn, [data-notifications]"
        );


    notificationButtons.forEach(button => {

        button.addEventListener("click", () => {

            toggleNotificationPanel();

        });

    });


    function toggleNotificationPanel() {

        let panel =
            document.querySelector(
                ".notification-panel"
            );


        if (!panel) {

            panel =
                createNotificationPanel();

        }


        panel.classList.toggle("visible");

    }

}


/* =========================================================
   CREATE NOTIFICATION PANEL
   ========================================================= */

function createNotificationPanel() {

    const panel =
        document.createElement("div");


    panel.className =
        "notification-panel";


    panel.innerHTML = `

        <div class="notification-header">

            <strong>Notifications</strong>

            <button
                class="notification-clear"
                type="button">
                Mark all as read
            </button>

        </div>

        <div class="notification-item">

            <span>●</span>

            <div>
                <strong>New announcement</strong>
                <small>Club administration</small>
            </div>

        </div>

        <div class="notification-item">

            <span>●</span>

            <div>
                <strong>Task reminder</strong>
                <small>You have an upcoming task</small>
            </div>

        </div>

    `;


    document.body.appendChild(panel);


    const button =
        document.querySelector(
            ".notification-btn, [data-notifications]"
        );


    if (button) {

        const rect =
            button.getBoundingClientRect();


        panel.style.top =
            `${rect.bottom + 10}px`;


        panel.style.right =
            `${window.innerWidth - rect.right}px`;

    }


    const clearButton =
        panel.querySelector(
            ".notification-clear"
        );


    clearButton.addEventListener(
        "click",
        () => {

            panel
                .querySelectorAll(
                    ".notification-item"
                )
                .forEach(item => {

                    item.style.opacity =
                        "0.45";

                });


            showToast(
                "Notifications marked as read"
            );

        }
    );


    return panel;

}


/* =========================================================
   11. CALENDAR
   ========================================================= */

function initCalendar() {

    const calendar =
        document.querySelector(
            ".calendar"
        );


    if (!calendar) return;


    const today =
        new Date();


    const currentMonth =
        today.getMonth();


    const currentYear =
        today.getFullYear();


    const monthNames = [

        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"

    ];


    const title =
        document.querySelector(
            ".calendar-title, [data-calendar-title]"
        );


    if (title) {

        title.textContent =
            `${monthNames[currentMonth]} ${currentYear}`;

    }


    /*
     * If the calendar already contains dates
     * from the HTML, keep them.
     *
     * Otherwise generate a simple calendar.
     */

    const existingDates =
        calendar.querySelectorAll(
            "span"
        );


    if (existingDates.length === 0) {

        generateCalendar();

    }


    function generateCalendar() {

        const firstDay =
            new Date(
                currentYear,
                currentMonth,
                1
            ).getDay();


        const daysInMonth =
            new Date(
                currentYear,
                currentMonth + 1,
                0
            ).getDate();


        calendar.innerHTML = `

            <b>Su</b>
            <b>Mo</b>
            <b>Tu</b>
            <b>We</b>
            <b>Th</b>
            <b>Fr</b>
            <b>Sa</b>

        `;


        let start =
            firstDay;


        if (start === 0) {

            start = 0;

        }


        for (
            let i = 0;
            i < start;
            i++
        ) {

            const empty =
                document.createElement("span");

            empty.innerHTML = "";

            calendar.appendChild(empty);

        }


        for (
            let day = 1;
            day <= daysInMonth;
            day++
        ) {

            const date =
                document.createElement("span");


            date.textContent =
                day;


            if (day === today.getDate()) {

                date.classList.add(
                    "today"
                );

            }


            date.addEventListener(
                "click",
                () => {

                    document
                        .querySelectorAll(
                            ".calendar span"
                        )
                        .forEach(
                            element =>
                                element.classList.remove(
                                    "selected"
                                )
                        );


                    date.classList.add(
                        "selected"
                    );


                    showToast(
                        `Selected ${day} ${monthNames[currentMonth]}`
                    );

                }
            );


            calendar.appendChild(date);

        }

    }

}


/* =========================================================
   12. PROFILE EDIT
   ========================================================= */

function initProfile() {

    const editButton =
        document.querySelector(
            "[data-edit-profile], #editProfile"
        );


    if (!editButton) return;


    const inputs =
        document.querySelectorAll(
            ".profile-details input, .profile-details textarea"
        );


    let editing = false;


    editButton.addEventListener(
        "click",
        () => {

            editing =
                !editing;


            inputs.forEach(input => {

                input.disabled =
                    !editing;

            });


            editButton.textContent =
                editing
                    ? "Save changes"
                    : "Edit profile";


            if (!editing) {

                showToast(
                    "Profile updated"
                );

            }

        }
    );

}


/* =========================================================
   13. GENERIC BUTTON INTERACTIONS
   ========================================================= */

function initButtons() {

    const actionButtons =
        document.querySelectorAll(
            "[data-action]"
        );


    actionButtons.forEach(button => {

        if (
            button.dataset.action ===
            "login"
        ) {

            return;

        }


        button.addEventListener(
            "click",
            () => {

                const action =
                    button.dataset.action;


                switch (action) {

                    case "download":

                        showToast(
                            "Preparing document..."
                        );

                        break;


                    case "register":

                        showToast(
                            "Registration opened"
                        );

                        break;


                    case "join":

                        showToast(
                            "Registration request started"
                        );

                        break;


                    case "share":

                        shareContent();

                        break;


                    default:

                        break;

                }

            }
        );

    });

}


/* =========================================================
   14. SHARE
   ========================================================= */

function shareContent() {

    if (
        navigator.share
    ) {

        navigator.share({

            title:
                "ORSC — Operations Research Society Club",

            text:
                "Discover the ORSC Club Management System.",

            url:
                window.location.href

        }).catch(() => {});

    }

    else {

        navigator.clipboard
            ?.writeText(
                window.location.href
            );


        showToast(
            "Link copied"
        );

    }

}


/* =========================================================
   15. TOAST SYSTEM
   ========================================================= */

function showToast(message) {

    let toast =
        document.querySelector(
            ".toast"
        );


    if (!toast) {

        toast =
            document.createElement(
                "div"
            );


        toast.className =
            "toast";


        document.body.appendChild(
            toast
        );

    }


    toast.textContent =
        message;


    toast.classList.add(
        "show"
    );


    clearTimeout(
        window.toastTimer
    );


    window.toastTimer =
        setTimeout(() => {

            toast.classList.remove(
                "show"
            );

        }, 2500);

}


/* =========================================================
   16. SEARCH
   ========================================================= */

const searchInput =
    document.querySelector(
        ".search input"
    );


if (searchInput) {

    searchInput.addEventListener(
        "input",
        () => {

            const query =
                searchInput.value
                    .trim()
                    .toLowerCase();


            if (!query) {

                showAllSearchableItems();

                return;

            }


            const searchable =
                document.querySelectorAll(
                    ".event-card, .document-card, .announcement-feed article, .department-card"
                );


            searchable.forEach(item => {

                const text =
                    item.textContent
                        .toLowerCase();


                item.style.display =
                    text.includes(query)
                        ? ""
                        : "none";

            });

        }
    );

}


function showAllSearchableItems() {

    document.querySelectorAll(
        ".event-card, .document-card, .announcement-feed article, .department-card"
    ).forEach(item => {

        item.style.display = "";

    });

}


/* =========================================================
   17. COUNTDOWN
   ========================================================= */

function initCountdown() {

    const countdown =
        document.querySelector(
            ".countdown"
        );


    if (!countdown) return;


    const targetDate =
        countdown.dataset.date;


    if (!targetDate) return;


    const target =
        new Date(targetDate).getTime();


    const days =
        countdown.querySelector(
            "[data-days]"
        );


    const hours =
        countdown.querySelector(
            "[data-hours]"
        );


    const minutes =
        countdown.querySelector(
            "[data-minutes]"
        );


    const seconds =
        countdown.querySelector(
            "[data-seconds]"
        );


    function updateCountdown() {

        const now =
            Date.now();


        const difference =
            target - now;


        if (difference <= 0) {

            if (days) days.textContent = "00";

            if (hours) hours.textContent = "00";

            if (minutes) minutes.textContent = "00";

            if (seconds) seconds.textContent = "00";

            return;

        }


        const totalSeconds =
            Math.floor(
                difference / 1000
            );


        const d =
            Math.floor(
                totalSeconds / 86400
            );


        const h =
            Math.floor(
                (totalSeconds % 86400) / 3600
            );


        const m =
            Math.floor(
                (totalSeconds % 3600) / 60
            );


        const s =
            totalSeconds % 60;


        if (days) {

            days.textContent =
                String(d).padStart(2, "0");

        }


        if (hours) {

            hours.textContent =
                String(h).padStart(2, "0");

        }


        if (minutes) {

            minutes.textContent =
                String(m).padStart(2, "0");

        }


        if (seconds) {

            seconds.textContent =
                String(s).padStart(2, "0");

        }

    }


    updateCountdown();


    setInterval(
        updateCountdown,
        1000
    );

}


initCountdown();


/* =========================================================
   18. SMOOTH BUTTON RIPPLE
   ========================================================= */

document.addEventListener(
    "click",
    event => {

        const button =
            event.target.closest(
                ".btn, .nav-item, .quick-grid button, .member-shortcuts button"
            );


        if (!button) return;


        const ripple =
            document.createElement(
                "span"
            );


        ripple.className =
            "ripple";


        button.appendChild(
            ripple
        );


        setTimeout(() => {

            ripple.remove();

        }, 500);

    }
);


/* =========================================================
   19. ACTIVE NAVIGATION ON PAGE LOAD
   ========================================================= */

function activateFirstPage() {

    const activePage =
        document.querySelector(
            ".page.active"
        );


    if (activePage) {

        const pageId =
            activePage.id;


        document
            .querySelectorAll(
                "[data-page]"
            )
            .forEach(item => {

                if (
                    item.dataset.page ===
                    pageId
                ) {

                    item.classList.add(
                        "active"
                    );

                }

            });

    }

}


activateFirstPage();


/* =========================================================
   20. PREVENT EMPTY LINKS
   ========================================================= */

document.addEventListener(
    "click",
    event => {

        const link =
            event.target.closest(
                'a[href="#"]'
            );


        if (link) {

            event.preventDefault();

        }

    }
);


/* =========================================================
   END ORSC JAVASCRIPT
   ========================================================= */