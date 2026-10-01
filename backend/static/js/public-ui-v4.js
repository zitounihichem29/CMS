"use strict";


document.addEventListener(
    "DOMContentLoaded",
    function () {


        /* =====================================================
           ELEMENTS
        ===================================================== */

        const body =
            document.body;

        const navbar =
            document.querySelector(
                ".navbar"
            );

        const themeButton =
            document.getElementById(
                "themeToggle"
            );

        const mobileMenu =
            document.getElementById(
                "mobileMenu"
            );

        const mobileMenuButton =
            document.getElementById(
                "mobileMenuButton"
            );


        /* =====================================================
           SCROLL PROGRESS
        ===================================================== */

        const progress =
            document.createElement(
                "div"
            );


        progress.className =
            "public-scroll-progress";


        body.appendChild(
            progress
        );


        function updateScrollProgress() {

            const documentHeight =
                document.documentElement
                    .scrollHeight
                -
                window.innerHeight;


            const current =
                window.scrollY;


            const percentage =
                documentHeight > 0
                    ?
                    (
                        current
                        /
                        documentHeight
                    )
                    * 100
                    :
                    0;


            progress.style.width =
                Math.min(
                    100,
                    Math.max(
                        0,
                        percentage
                    )
                )
                + "%";

        }


        updateScrollProgress();


        window.addEventListener(
            "scroll",
            updateScrollProgress,
            {
                passive:
                    true
            }
        );


        /* =====================================================
           NAVBAR SCROLL STATE
        ===================================================== */

        function updateNavbar() {

            if (!navbar) {

                return;

            }


            navbar.classList.toggle(
                "public-navbar-scrolled",
                window.scrollY > 24
            );

        }


        updateNavbar();


        window.addEventListener(
            "scroll",
            updateNavbar,
            {
                passive:
                    true
            }
        );


        /* =====================================================
           THEME ICON
           Existing public.js still manages the theme.
           This only synchronizes the icon.
        ===================================================== */

        function updateThemeIcon() {

            if (!themeButton) {

                return;

            }


            const dark =
                body.classList
                    .contains(
                        "dark-mode"
                    );


            themeButton.textContent =
                dark
                    ? "☀"
                    : "☾";


            themeButton.setAttribute(
                "title",
                dark
                    ?
                    "Switch to light mode"
                    :
                    "Switch to dark mode"
            );

        }


        updateThemeIcon();


        const themeObserver =
            new MutationObserver(
                function () {

                    updateThemeIcon();

                }
            );


        themeObserver.observe(
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
           REVEAL ANIMATIONS
        ===================================================== */

        const selectors = [

            ".final-home-copy",

            ".final-home-visual",

            ".final-home-stat",

            ".final-section-heading",

            ".final-mission-card",

            ".final-activity",

            ".final-pathway",

            ".final-cta",

            ".event-card",

            ".training-card",

            ".department-card",

            ".public-project-card",

            ".public-article-card",

            ".gallery-item",

            ".public-alumni-card"

        ];


        const revealElements =
            document.querySelectorAll(
                selectors.join(
                    ","
                )
            );


        revealElements.forEach(
            function (
                element,
                index
            ) {

                element.classList.add(
                    "public-reveal"
                );


                element.style
                    .transitionDelay =
                        Math.min(
                            index
                            * 24,
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
                                    !entry.isIntersecting
                                ) {

                                    return;

                                }


                                entry.target
                                    .classList
                                    .add(
                                        "public-visible"
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
                            0.07,

                        rootMargin:
                            "0px 0px -24px 0px"
                    }
                );


            revealElements.forEach(
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

            revealElements.forEach(
                function (
                    element
                ) {

                    element.classList.add(
                        "public-visible"
                    );

                }
            );

        }


        /* =====================================================
           MOBILE MENU
        ===================================================== */

        function closeMobileMenu() {

            if (!mobileMenu) {

                return;

            }


            mobileMenu.classList.remove(
                "open"
            );


            if (mobileMenuButton) {

                mobileMenuButton.setAttribute(
                    "aria-expanded",
                    "false"
                );

                mobileMenuButton.textContent =
                    "☰";

            }

        }


        if (mobileMenuButton) {

            mobileMenuButton.setAttribute(
                "aria-expanded",
                mobileMenu
                &&
                mobileMenu.classList
                    .contains(
                        "open"
                    )
                    ?
                    "true"
                    :
                    "false"
            );


            mobileMenuButton.addEventListener(
                "click",
                function () {

                    window.setTimeout(
                        function () {

                            const opened =
                                mobileMenu
                                &&
                                mobileMenu
                                    .classList
                                    .contains(
                                        "open"
                                    );


                            mobileMenuButton
                                .setAttribute(
                                    "aria-expanded",
                                    opened
                                    ?
                                    "true"
                                    :
                                    "false"
                                );


                            mobileMenuButton
                                .textContent =
                                    opened
                                    ?
                                    "×"
                                    :
                                    "☰";

                        },
                        0
                    );

                }
            );

        }


        if (mobileMenu) {

            mobileMenu
                .querySelectorAll(
                    "a"
                )
                .forEach(
                    function (
                        link
                    ) {

                        link.addEventListener(
                            "click",
                            closeMobileMenu
                        );

                    }
                );

        }


        document.addEventListener(
            "keydown",
            function (
                event
            ) {

                if (
                    event.key
                    === "Escape"
                ) {

                    closeMobileMenu();

                }

            }
        );


        window.addEventListener(
            "resize",
            function () {

                if (
                    window.innerWidth
                    > 800
                ) {

                    closeMobileMenu();

                }

            }
        );


        /* =====================================================
           EXTERNAL LINKS
        ===================================================== */

        document
            .querySelectorAll(
                'a[target="_blank"]'
            )
            .forEach(
                function (
                    link
                ) {

                    if (
                        !link.rel
                    ) {

                        link.rel =
                            "noopener noreferrer";

                    }

                }
            );


        /* =====================================================
           ACTIVE MOBILE HOME LINK
        ===================================================== */

        if (
            window.location.pathname
            === "/website"
            &&
            mobileMenu
        ) {

            const firstLink =
                mobileMenu.querySelector(
                    'a[href$="/website"]'
                );


            if (firstLink) {

                firstLink.classList.add(
                    "active"
                );

            }

        }


    }
);