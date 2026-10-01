"use strict";


document.addEventListener(
    "DOMContentLoaded",
    function () {


        /* =====================================================
           ROOT
        ===================================================== */

        const body =
            document.body;

        const pageContent =
            document.querySelector(
                ".page-content"
            );

        const topbar =
            document.querySelector(
                ".topbar"
            );

        const searchBox =
            document.querySelector(
                ".cms-global-search"
            );

        const searchInput =
            document.getElementById(
                "cmsGlobalSearch"
            );


        body.classList.add(
            "ui-ready"
        );


        /* =====================================================
           PAGE ENTRANCE
        ===================================================== */

        if (pageContent) {

            pageContent.classList.add(
                "ui-page-enter"
            );

        }


        /* =====================================================
           TOPBAR PAGE CONTEXT
        ===================================================== */

        function findPageTitle() {

            if (!pageContent) {

                return null;

            }


            const title =
                pageContent.querySelector(
                    "h1"
                );


            if (!title) {

                return null;

            }


            const value =
                title.textContent
                    .replace(
                        /\s+/g,
                        " "
                    )
                    .trim();


            return (
                value
                || null
            );

        }


        function createPageContext() {

            if (
                !topbar
                || !searchBox
            ) {

                return;

            }


            if (
                topbar.querySelector(
                    ".cms-page-context"
                )
            ) {

                return;

            }


            const title =
                findPageTitle();


            if (!title) {

                return;

            }


            const context =
                document.createElement(
                    "div"
                );


            context.className =
                "cms-page-context";


            const label =
                document.createElement(
                    "span"
                );


            label.className =
                "cms-page-context-label";


            label.textContent =
                "ORSC CMS";


            const pageTitle =
                document.createElement(
                    "span"
                );


            pageTitle.className =
                "cms-page-context-title";


            pageTitle.textContent =
                title;


            context.appendChild(
                label
            );


            context.appendChild(
                pageTitle
            );


            topbar.insertBefore(
                context,
                searchBox
            );

        }


        createPageContext();


        /* =====================================================
           SEARCH SHORTCUT
        ===================================================== */

        function addSearchShortcut() {

            if (
                !searchBox
                || !searchInput
            ) {

                return;

            }


            if (
                searchBox.querySelector(
                    ".cms-search-shortcut"
                )
            ) {

                return;

            }


            const badge =
                document.createElement(
                    "span"
                );


            badge.className =
                "cms-search-shortcut";


            const isMac =
                navigator.platform
                    .toUpperCase()
                    .includes(
                        "MAC"
                    );


            badge.textContent =
                isMac
                    ? "⌘ K"
                    : "Ctrl K";


            searchBox.appendChild(
                badge
            );

        }


        addSearchShortcut();


        document.addEventListener(
            "keydown",
            function (event) {


                const target =
                    event.target;


                const isTyping =
                    target
                    instanceof
                    HTMLInputElement
                    ||
                    target
                    instanceof
                    HTMLTextAreaElement
                    ||
                    target
                    instanceof
                    HTMLSelectElement
                    ||
                    target
                    ?.isContentEditable;


                if (
                    (
                        event.ctrlKey
                        ||
                        event.metaKey
                    )
                    &&
                    event.key
                        .toLowerCase()
                    === "k"
                ) {

                    event.preventDefault();


                    if (searchInput) {

                        searchInput.focus();

                        searchInput.select();

                    }


                    return;

                }


                if (
                    event.key === "/"
                    &&
                    !isTyping
                    &&
                    searchInput
                ) {

                    event.preventDefault();

                    searchInput.focus();

                }

            }
        );


        /* =====================================================
           ACTIVE NAV ACCESSIBILITY
        ===================================================== */

        const activeNav =
            document.querySelector(
                ".sidebar-nav .nav-item.active"
            );


        if (activeNav) {

            activeNav.setAttribute(
                "aria-current",
                "page"
            );


            window.setTimeout(
                function () {

                    activeNav.scrollIntoView(
                        {
                            block:
                                "nearest",

                            behavior:
                                "smooth"
                        }
                    );

                },
                180
            );

        }


        /* =====================================================
           SIDEBAR NAV TOOLTIPS
           Helpful if text becomes visually narrow.
        ===================================================== */

        document
            .querySelectorAll(
                ".sidebar-nav .nav-item"
            )
            .forEach(
                function (item) {


                    const textElement =
                        item.querySelector(
                            "span:last-child"
                        );


                    if (!textElement) {

                        return;

                    }


                    const label =
                        textElement.textContent
                            .replace(
                                /\s+/g,
                                " "
                            )
                            .trim();


                    if (label) {

                        item.setAttribute(
                            "title",
                            label
                        );

                    }

                }
            );


        /* =====================================================
           REVEAL ANIMATIONS
        ===================================================== */

        const revealSelectors = [

            ".welcome-section",

            ".quick-card",

            ".activity-empty",

            ".dashboard-card",

            ".stat-card",

            ".member-card",

            ".department-card",

            ".project-card",

            ".event-card",

            ".training-card",

            ".article-card",

            ".organization-card",

            ".application-card",

            ".announcement-card",

            ".template-card",

            ".task-card",

            ".records-card",

            ".records-section",

            ".alumni-card",

            ".alumni-stat",

            ".alumni-form-card",

            ".alumni-hero"

        ];


        const revealItems =
            document.querySelectorAll(
                revealSelectors.join(
                    ","
                )
            );


        revealItems.forEach(
            function (
                element,
                index
            ) {

                element.classList.add(
                    "ui-reveal"
                );


                element.style
                    .transitionDelay =
                        Math.min(
                            index * 25,
                            180
                        )
                        + "ms";

            }
        );


        if (
            "IntersectionObserver"
            in window
        ) {

            const observer =
                new IntersectionObserver(
                    function (
                        entries,
                        currentObserver
                    ) {

                        entries.forEach(
                            function (
                                entry
                            ) {

                                if (
                                    !entry
                                        .isIntersecting
                                ) {

                                    return;

                                }


                                entry.target
                                    .classList
                                    .add(
                                        "ui-visible"
                                    );


                                currentObserver
                                    .unobserve(
                                        entry.target
                                    );

                            }
                        );

                    },
                    {
                        threshold:
                            0.05,

                        rootMargin:
                            "0px 0px -20px 0px"
                    }
                );


            revealItems.forEach(
                function (
                    element
                ) {

                    observer.observe(
                        element
                    );

                }
            );

        }

        else {

            revealItems.forEach(
                function (
                    element
                ) {

                    element.classList.add(
                        "ui-visible"
                    );

                }
            );

        }


        /* =====================================================
           TABLE ENHANCEMENT
        ===================================================== */

        document
            .querySelectorAll(
                ".page-content table"
            )
            .forEach(
                function (table) {

                    table.setAttribute(
                        "data-ui-table",
                        "true"
                    );

                }
            );


        /* =====================================================
           BUTTON FEEDBACK
        ===================================================== */

        document
            .querySelectorAll(
                [
                    ".page-content button",
                    ".page-content .btn",
                    ".page-content .records-btn"
                ].join(
                    ","
                )
            )
            .forEach(
                function (button) {


                    button.addEventListener(
                        "pointerdown",
                        function () {

                            button
                                .classList
                                .add(
                                    "ui-pressed"
                                );

                        }
                    );


                    [
                        "pointerup",
                        "pointercancel",
                        "pointerleave"
                    ]
                        .forEach(
                            function (
                                eventName
                            ) {

                                button.addEventListener(
                                    eventName,
                                    function () {

                                        button
                                            .classList
                                            .remove(
                                                "ui-pressed"
                                            );

                                    }
                                );

                            }
                        );

                }
            );


        /* =====================================================
           MOBILE — CLOSE SIDEBAR AFTER NAVIGATION
        ===================================================== */

        const sidebar =
            document.querySelector(
                ".sidebar"
            );


        const overlay =
            document.querySelector(
                "[data-mobile-sidebar-overlay]"
            );


        const menuToggle =
            document.querySelector(
                "[data-mobile-menu-toggle]"
            );


        function closeMobileSidebar() {

            if (
                window.innerWidth
                > 800
            ) {

                return;

            }


            if (sidebar) {

                sidebar.classList.remove(
                    "open",
                    "active",
                    "mobile-open"
                );

            }


            if (overlay) {

                overlay.classList.remove(
                    "active",
                    "open",
                    "visible"
                );

            }


            if (menuToggle) {

                menuToggle.setAttribute(
                    "aria-expanded",
                    "false"
                );

            }


            body.classList.remove(
                "sidebar-open",
                "mobile-sidebar-open"
            );

        }


        document
            .querySelectorAll(
                ".sidebar-nav .nav-item"
            )
            .forEach(
                function (link) {

                    link.addEventListener(
                        "click",
                        function () {

                            closeMobileSidebar();

                        }
                    );

                }
            );


        /* =====================================================
           ESCAPE
        ===================================================== */

        document.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key
                    !== "Escape"
                ) {

                    return;

                }


                if (
                    searchInput
                    &&
                    document.activeElement
                    === searchInput
                ) {

                    searchInput.blur();

                }


                closeMobileSidebar();

            }
        );


        /* =====================================================
           THEME ICON REFRESH
        ===================================================== */

        const themeToggle =
            document.getElementById(
                "themeToggle"
            );


        function refreshThemeIcon() {

            if (!themeToggle) {

                return;

            }


            const dark =
                body.classList
                    .contains(
                        "dark"
                    );


            themeToggle.textContent =
                dark
                    ? "☀"
                    : "☾";


            themeToggle.setAttribute(
                "title",
                dark
                    ? "Switch to light mode"
                    : "Switch to dark mode"
            );

        }


        refreshThemeIcon();


        if (themeToggle) {

            themeToggle.addEventListener(
                "click",
                function () {

                    window.setTimeout(
                        refreshThemeIcon,
                        0
                    );

                }
            );

        }


        const bodyObserver =
            new MutationObserver(
                function (
                    mutations
                ) {

                    const themeChanged =
                        mutations.some(
                            function (
                                mutation
                            ) {

                                return (
                                    mutation.type
                                    === "attributes"
                                    &&
                                    mutation
                                        .attributeName
                                    === "class"
                                );

                            }
                        );


                    if (themeChanged) {

                        refreshThemeIcon();

                    }

                }
            );


        bodyObserver.observe(
            body,
            {
                attributes:
                    true,

                attributeFilter:
                    [
                        "class"
                    ]
            }
        );


        /* =====================================================
           RESIZE CLEANUP
        ===================================================== */

        window.addEventListener(
            "resize",
            function () {

                if (
                    window.innerWidth
                    > 800
                ) {

                    body.classList.remove(
                        "sidebar-open",
                        "mobile-sidebar-open"
                    );

                }

            }
        );


    }
);