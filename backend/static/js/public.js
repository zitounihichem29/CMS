/* =========================================================
   PUBLIC EVENT COUNTDOWN
   ========================================================= */

const publicEventCountdown =
    document.getElementById("publicEventCountdown");


if (publicEventCountdown) {

    const targetValue =
        publicEventCountdown.dataset.target;

    const targetDate =
        new Date(targetValue);


    const daysElement =
        document.getElementById(
            "publicCountdownDays"
        );

    const hoursElement =
        document.getElementById(
            "publicCountdownHours"
        );

    const minutesElement =
        document.getElementById(
            "publicCountdownMinutes"
        );

    const secondsElement =
        document.getElementById(
            "publicCountdownSeconds"
        );


    function updatePublicEventCountdown() {

        const now = new Date();

        const difference =
            targetDate.getTime()
            - now.getTime();


        /* EVENT STARTED */

        if (difference <= 0) {

            daysElement.textContent = "00";
            hoursElement.textContent = "00";
            minutesElement.textContent = "00";
            secondsElement.textContent = "00";

            clearInterval(
                publicCountdownInterval
            );


            /*
             * Reload page so Flask changes
             * the event status to:
             *
             * Event in Progress
             */

            window.location.reload();

            return;
        }


        /* CALCULATIONS */

        const days = Math.floor(
            difference
            / (1000 * 60 * 60 * 24)
        );


        const hours = Math.floor(
            (
                difference
                % (1000 * 60 * 60 * 24)
            )
            / (1000 * 60 * 60)
        );


        const minutes = Math.floor(
            (
                difference
                % (1000 * 60 * 60)
            )
            / (1000 * 60)
        );


        const seconds = Math.floor(
            (
                difference
                % (1000 * 60)
            )
            / 1000
        );


        /* DISPLAY */

        daysElement.textContent =
            String(days).padStart(
                2,
                "0"
            );

        hoursElement.textContent =
            String(hours).padStart(
                2,
                "0"
            );

        minutesElement.textContent =
            String(minutes).padStart(
                2,
                "0"
            );

        secondsElement.textContent =
            String(seconds).padStart(
                2,
                "0"
            );
    }


    /* FIRST CALCULATION */

    updatePublicEventCountdown();


    /* UPDATE EVERY SECOND */

    const publicCountdownInterval =
        setInterval(
            updatePublicEventCountdown,
            1000
        );

}




/* =========================================================
   RESEARCH & INNOVATION TABS
   ========================================================= */

const researchTabs =
    document.querySelectorAll(".public-research-tab");

const researchContents =
    document.querySelectorAll(".public-research-content");


researchTabs.forEach(function (tab) {

    tab.addEventListener("click", function () {

        const targetId =
            tab.dataset.target;


        /* REMOVE ACTIVE FROM ALL TABS */

        researchTabs.forEach(function (item) {
            item.classList.remove("active");
        });


        /* REMOVE ACTIVE FROM ALL CONTENT */

        researchContents.forEach(function (content) {
            content.classList.remove("active");
        });


        /* ACTIVATE CLICKED TAB */

        tab.classList.add("active");


        /* SHOW CORRESPONDING SECTION */

        const targetSection =
            document.getElementById(targetId);

        if (targetSection) {
            targetSection.classList.add("active");
        }

    });

});





/* =========================================================
   RESEARCH & INNOVATION
   IT PROJECT MODAL
   ========================================================= */

const publicProjectCards =
    document.querySelectorAll(".public-project-card");

const publicProjectModal =
    document.getElementById("publicProjectModal");

const publicProjectModalClose =
    document.getElementById("publicProjectModalClose");

const publicProjectModalOverlay =
    publicProjectModal
        ? publicProjectModal.querySelector(
            ".public-research-modal-overlay"
        )
        : null;


if (publicProjectCards.length && publicProjectModal) {

    const modalTitle =
        document.getElementById("publicProjectModalTitle");

    const modalDescription =
        document.getElementById("publicProjectModalDescription");

    const modalOwner =
        document.getElementById("publicProjectModalOwner");

    const modalTeam =
        document.getElementById("publicProjectModalTeam");

    const modalActions =
        document.getElementById("publicProjectModalActions");

    const modalLink =
        document.getElementById("publicProjectModalLink");


    function openProjectModal(card) {

        const hiddenData =
            card.querySelector(".public-project-hidden-data");

        if (!hiddenData) {
            return;
        }


        const title =
            hiddenData.querySelector(
                ".public-project-title"
            )?.textContent.trim() || "";


        const description =
            hiddenData.querySelector(
                ".public-project-description"
            )?.textContent.trim() || "";


        const owner =
            hiddenData.querySelector(
                ".public-project-owner"
            )?.textContent.trim() || "";


        const team =
            hiddenData.querySelector(
                ".public-project-team"
            )?.textContent.trim() || "";


        const projectLink =
            hiddenData.querySelector(
                ".public-project-link"
            )?.textContent.trim() || "";


        /* TITLE */

        modalTitle.textContent =
            title || "Untitled Project";


        /* DESCRIPTION */

        modalDescription.textContent =
            description || "No description available.";


        /* IDEA OWNER */

        modalOwner.textContent =
            owner || "Not specified";


        /* TEAM */

        modalTeam.textContent =
            team || "No final project team listed.";


        /* LINK */

        if (projectLink) {

            modalLink.href = projectLink;

            modalActions.style.display = "flex";

        } else {

            modalLink.removeAttribute("href");

            modalActions.style.display = "none";

        }


        /* OPEN MODAL */

        publicProjectModal.classList.add("open");

        publicProjectModal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.style.overflow = "hidden";
    }


    function closeProjectModal() {

        publicProjectModal.classList.remove("open");

        publicProjectModal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.style.overflow = "";
    }


    /* OPEN CARD */

    publicProjectCards.forEach(function (card) {

        card.addEventListener("click", function () {

            openProjectModal(card);

        });

    });


    /* CLOSE BUTTON */

    if (publicProjectModalClose) {

        publicProjectModalClose.addEventListener(
            "click",
            closeProjectModal
        );

    }


    /* CLOSE BY OVERLAY */

    if (publicProjectModalOverlay) {

        publicProjectModalOverlay.addEventListener(
            "click",
            closeProjectModal
        );

    }


    /* CLOSE WITH ESCAPE */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
                &&
                publicProjectModal.classList.contains("open")
            ) {

                closeProjectModal();

            }

        }
    );

}




// ============================================================
// SCIENTIFIC ARTICLE MODAL
// ============================================================

const publicArticleCards =
    document.querySelectorAll(".public-article-card");

const publicArticleModal =
    document.getElementById("publicArticleModal");

const publicArticleModalClose =
    document.getElementById("publicArticleModalClose");

const publicArticleModalOverlay =
    publicArticleModal
        ? publicArticleModal.querySelector(
            ".public-research-modal-overlay"
        )
        : null;


if (
    publicArticleCards.length
    && publicArticleModal
) {

    const modalTitle =
        document.getElementById(
            "publicArticleModalTitle"
        );

    const modalDescription =
        document.getElementById(
            "publicArticleModalDescription"
        );

    const modalOwner =
        document.getElementById(
            "publicArticleModalOwner"
        );

    const modalAuthors =
        document.getElementById(
            "publicArticleModalAuthors"
        );

    const modalLink =
        document.getElementById(
            "publicArticleModalLink"
        );


    function openArticleModal(card) {

        const hiddenData =
            card.querySelector(
                ".public-article-hidden-data"
            );


        if (!hiddenData) {
            return;
        }


        const title =
            hiddenData.querySelector(
                ".public-article-title"
            )?.textContent.trim() || "";


        const description =
            hiddenData.querySelector(
                ".public-article-description"
            )?.textContent.trim() || "";


        const owner =
            hiddenData.querySelector(
                ".public-article-owner"
            )?.textContent.trim() || "";


        const authors =
            hiddenData.querySelector(
                ".public-article-authors"
            )?.textContent.trim() || "";


        const articleId =
            hiddenData.querySelector(
                ".public-article-id"
            )?.textContent.trim() || "";


        modalTitle.textContent =
            title || "Untitled Article";


        modalDescription.textContent =
            description
            || "No description available.";


        modalOwner.textContent =
            owner || "Not specified";


        modalAuthors.textContent =
            authors || "No authors listed.";


        if (articleId) {

            modalLink.href =
                "/website/articles/"
                + articleId
                + "/pdf";

        }


        publicArticleModal.classList.add(
            "open"
        );


        publicArticleModal.setAttribute(
            "aria-hidden",
            "false"
        );


        document.body.style.overflow =
            "hidden";
    }



    function closeArticleModal() {

        publicArticleModal.classList.remove(
            "open"
        );


        publicArticleModal.setAttribute(
            "aria-hidden",
            "true"
        );


        document.body.style.overflow =
            "";
    }



    publicArticleCards.forEach(
        function (card) {

            card.addEventListener(
                "click",
                function () {

                    openArticleModal(card);

                }
            );

        }
    );


    if (publicArticleModalClose) {

        publicArticleModalClose.addEventListener(
            "click",
            closeArticleModal
        );

    }


    if (publicArticleModalOverlay) {

        publicArticleModalOverlay.addEventListener(
            "click",
            closeArticleModal
        );

    }


    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
                && publicArticleModal
                    .classList.contains("open")
            ) {

                closeArticleModal();

            }

        }
    );

}






/* ============================================================
   PUBLIC TRAININGS
   UPCOMING TRAINING MODAL
   ============================================================ */

const publicTrainingCards =
    document.querySelectorAll(
        ".public-training-open"
    );

const publicTrainingModal =
    document.getElementById(
        "publicTrainingModal"
    );

const publicTrainingModalOverlay =
    publicTrainingModal
        ? publicTrainingModal.querySelector(
            ".public-training-modal-overlay"
        )
        : null;

const publicTrainingModalClose =
    document.getElementById(
        "publicTrainingModalClose"
    );


/* ============================================================
   MODAL ELEMENTS
   ============================================================ */

const publicTrainingModalImage =
    document.getElementById(
        "publicTrainingModalImage"
    );

const publicTrainingModalTitle =
    document.getElementById(
        "publicTrainingModalTitle"
    );

const publicTrainingModalDescription =
    document.getElementById(
        "publicTrainingModalDescription"
    );

const publicTrainingModalCoach =
    document.getElementById(
        "publicTrainingModalCoach"
    );

const publicTrainingModalProfession =
    document.getElementById(
        "publicTrainingModalProfession"
    );

const publicTrainingModalDate =
    document.getElementById(
        "publicTrainingModalDate"
    );

const publicTrainingModalTime =
    document.getElementById(
        "publicTrainingModalTime"
    );

const publicTrainingModalLocation =
    document.getElementById(
        "publicTrainingModalLocation"
    );

const publicTrainingModalTerm =
    document.getElementById(
        "publicTrainingModalTerm"
    );

const publicTrainingRegistration =
    document.getElementById(
        "publicTrainingRegistration"
    );

const publicTrainingRegisterButton =
    document.getElementById(
        "publicTrainingRegisterButton"
    );


/* ============================================================
   HELPERS
   ============================================================ */

function getTrainingData(
    card,
    selector
) {

    const element =
        card.querySelector(selector);

    if (!element) {
        return "";
    }

    return element
        .textContent
        .trim();
}


function formatTrainingDate(
    value
) {

    if (!value) {
        return "Date TBD";
    }

    const parts =
        value.split("-");

    if (parts.length !== 3) {
        return value;
    }

    const year =
        Number(parts[0]);

    const month =
        Number(parts[1]) - 1;

    const day =
        Number(parts[2]);

    const date =
        new Date(
            year,
            month,
            day
        );

    return date.toLocaleDateString(
        "en-US",
        {
            day: "numeric",
            month: "long",
            year: "numeric"
        }
    );
}


function formatTrainingTime(
    value
) {

    if (!value) {
        return "";
    }

    return value
        .substring(0, 5);
}


/* ============================================================
   OPEN MODAL
   ============================================================ */

function openPublicTrainingModal(
    card
) {

    if (!publicTrainingModal) {
        return;
    }


    const title =
        getTrainingData(
            card,
            ".training-data-title"
        );


    const description =
        getTrainingData(
            card,
            ".training-data-description"
        );


    const coach =
        getTrainingData(
            card,
            ".training-data-coach"
        );


    const profession =
        getTrainingData(
            card,
            ".training-data-profession"
        );


    const date =
        getTrainingData(
            card,
            ".training-data-date"
        );


    const startTime =
        getTrainingData(
            card,
            ".training-data-start"
        );


    const endTime =
        getTrainingData(
            card,
            ".training-data-end"
        );


    const location =
        getTrainingData(
            card,
            ".training-data-location"
        );


    const term =
        getTrainingData(
            card,
            ".training-data-term"
        );


    const image =
        getTrainingData(
            card,
            ".training-data-image"
        );


    const registrationLink =
        getTrainingData(
            card,
            ".training-data-registration"
        );


    /* ========================================================
       TEXT
       ======================================================== */

    publicTrainingModalTitle.textContent =
        title || "Training";


    publicTrainingModalDescription.textContent =
        description ||
        "No description available.";


    publicTrainingModalCoach.textContent =
        coach ||
        "Not specified";


    publicTrainingModalProfession.textContent =
        profession;


    publicTrainingModalDate.textContent =
        formatTrainingDate(date);


    /* ========================================================
       TIME
       ======================================================== */

    const formattedStart =
        formatTrainingTime(
            startTime
        );

    const formattedEnd =
        formatTrainingTime(
            endTime
        );


    if (
        formattedStart &&
        formattedEnd
    ) {

        publicTrainingModalTime.textContent =
            formattedStart +
            " – " +
            formattedEnd;

    }

    else if (formattedStart) {

        publicTrainingModalTime.textContent =
            formattedStart;

    }

    else {

        publicTrainingModalTime.textContent =
            "Time TBD";

    }


    publicTrainingModalLocation.textContent =
        location ||
        "Location TBD";


    publicTrainingModalTerm.textContent =
        term ||
        "Not specified";


    /* ========================================================
       IMAGE
       ======================================================== */

    publicTrainingModalImage.innerHTML =
        "";


    if (image) {

        const img =
            document.createElement(
                "img"
            );

        img.src =
            image;

        img.alt =
            title ||
            "ORSC Training";

        publicTrainingModalImage
            .appendChild(img);

    }

    else {

        const placeholder =
            document.createElement(
                "div"
            );

        placeholder.className =
            "public-training-placeholder";

        placeholder.innerHTML = `
            <span>ORSC</span>
            <strong>TRAINING</strong>
        `;

        publicTrainingModalImage
            .appendChild(
                placeholder
            );

    }


    /* ========================================================
       REGISTRATION
       ======================================================== */

    if (
        registrationLink &&
        publicTrainingRegisterButton
    ) {

        try {

            const registrationUrl =
                new URL(
                    registrationLink,
                    window.location.origin
                );


            if (
                registrationUrl.protocol ===
                    "http:" ||
                registrationUrl.protocol ===
                    "https:"
            ) {

                publicTrainingRegisterButton.href =
                    registrationUrl.href;

                publicTrainingRegistration
                    .classList.remove(
                        "no-registration"
                    );

            }

            else {

                throw new Error(
                    "Invalid protocol"
                );

            }

        }

        catch (error) {

            publicTrainingRegisterButton.href =
                "#";

            publicTrainingRegistration
                .classList.add(
                    "no-registration"
                );

        }

    }

    else {

        publicTrainingRegisterButton.href =
            "#";

        publicTrainingRegistration
            .classList.add(
                "no-registration"
            );

    }


    /* ========================================================
       OPEN
       ======================================================== */

    publicTrainingModal.classList.add(
        "open"
    );

    publicTrainingModal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.style.overflow =
        "hidden";

}


/* ============================================================
   CLOSE MODAL
   ============================================================ */

function closePublicTrainingModal() {

    if (!publicTrainingModal) {
        return;
    }

    publicTrainingModal.classList.remove(
        "open"
    );

    publicTrainingModal.setAttribute(
        "aria-hidden",
        "true"
    );

    document.body.style.overflow =
        "";

}


/* ============================================================
   UPCOMING TRAINING CLICK
   ============================================================ */

publicTrainingCards.forEach(
    function (card) {

        card.addEventListener(
            "click",
            function () {

                openPublicTrainingModal(
                    card
                );

            }
        );

    }
);


/* ============================================================
   CLOSE BUTTON
   ============================================================ */

if (publicTrainingModalClose) {

    publicTrainingModalClose
        .addEventListener(
            "click",
            closePublicTrainingModal
        );

}


/* ============================================================
   OVERLAY
   ============================================================ */

if (publicTrainingModalOverlay) {

    publicTrainingModalOverlay
        .addEventListener(
            "click",
            closePublicTrainingModal
        );

}


/* ============================================================
   ESCAPE KEY
   ============================================================ */

document.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Escape" &&
            publicTrainingModal &&
            publicTrainingModal.classList
                .contains("open")
        ) {

            closePublicTrainingModal();

        }

    }
);




/* ============================================================
   PUBLIC GALLERY
   FILTERS + LIGHTBOX
   ============================================================ */

const publicGalleryFilters =
    document.querySelectorAll(
        ".public-gallery-filter"
    );

const publicGalleryItems =
    document.querySelectorAll(
        ".public-gallery-item"
    );

const publicGalleryLightbox =
    document.getElementById(
        "publicGalleryLightbox"
    );

const publicGalleryLightboxOverlay =
    document.getElementById(
        "publicGalleryLightboxOverlay"
    );

const publicGalleryLightboxClose =
    document.getElementById(
        "publicGalleryLightboxClose"
    );

const publicGalleryLightboxImage =
    document.getElementById(
        "publicGalleryLightboxImage"
    );

const publicGalleryLightboxTitle =
    document.getElementById(
        "publicGalleryLightboxTitle"
    );


/* ============================================================
   FILTERS
   ============================================================ */

publicGalleryFilters.forEach(
    function (filterButton) {

        filterButton.addEventListener(
            "click",
            function () {

                const selectedFilter =
                    filterButton.dataset
                        .galleryFilter;


                /* ACTIVE BUTTON */

                publicGalleryFilters.forEach(
                    function (button) {

                        button.classList.remove(
                            "active"
                        );

                    }
                );


                filterButton.classList.add(
                    "active"
                );


                /* FILTER IMAGES */

                publicGalleryItems.forEach(
                    function (item) {

                        const itemType =
                            item.dataset
                                .galleryType;


                        const shouldShow =
                            selectedFilter === "all"
                            ||
                            itemType === selectedFilter;


                        if (shouldShow) {

                            item.classList.remove(
                                "gallery-hidden"
                            );

                        } else {

                            item.classList.add(
                                "gallery-hidden"
                            );

                        }

                    }
                );

            }
        );

    }
);


/* ============================================================
   OPEN LIGHTBOX
   ============================================================ */

function openPublicGalleryLightbox(
    item
) {

    if (
        !publicGalleryLightbox
        ||
        !publicGalleryLightboxImage
        ||
        !publicGalleryLightboxTitle
    ) {
        return;
    }


    const image =
        item.dataset.galleryImage || "";

    const title =
        item.dataset.galleryTitle || "";


    if (!image) {
        return;
    }


    publicGalleryLightboxImage.src =
        image;

    publicGalleryLightboxImage.alt =
        title || "ORSC Gallery";


    publicGalleryLightboxTitle.textContent =
        title;


    publicGalleryLightbox.classList.add(
        "open"
    );


    publicGalleryLightbox.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.style.overflow =
        "hidden";
}


/* ============================================================
   CLOSE LIGHTBOX
   ============================================================ */

function closePublicGalleryLightbox() {

    if (!publicGalleryLightbox) {
        return;
    }


    publicGalleryLightbox.classList.remove(
        "open"
    );


    publicGalleryLightbox.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.style.overflow =
        "";


    if (publicGalleryLightboxImage) {

        publicGalleryLightboxImage.src =
            "";

        publicGalleryLightboxImage.alt =
            "";

    }

}


/* ============================================================
   IMAGE CLICK
   ============================================================ */

publicGalleryItems.forEach(
    function (item) {

        item.addEventListener(
            "click",
            function () {

                openPublicGalleryLightbox(
                    item
                );

            }
        );

    }
);


/* ============================================================
   CLOSE BUTTON
   ============================================================ */

if (publicGalleryLightboxClose) {

    publicGalleryLightboxClose
        .addEventListener(
            "click",
            closePublicGalleryLightbox
        );

}


/* ============================================================
   CLOSE BY OVERLAY
   ============================================================ */

if (publicGalleryLightboxOverlay) {

    publicGalleryLightboxOverlay
        .addEventListener(
            "click",
            closePublicGalleryLightbox
        );

}


/* ============================================================
   ESCAPE KEY
   ============================================================ */

document.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Escape"
            &&
            publicGalleryLightbox
            &&
            publicGalleryLightbox
                .classList
                .contains("open")
        ) {

            closePublicGalleryLightbox();

        }

    }
);










/* ============================================================
   PUBLIC CONTACT
   MESSAGE CHARACTER COUNTER
   ============================================================ */

const publicContactMessage =
    document.getElementById(
        "message"
    );

const publicContactCharacterCount =
    document.getElementById(
        "publicContactCharacterCount"
    );


if (
    publicContactMessage
    &&
    publicContactCharacterCount
) {

    function updatePublicContactCharacterCount() {

        const currentLength =
            publicContactMessage.value.length;

        publicContactCharacterCount.textContent =
            currentLength + " / 2000";
    }


    publicContactMessage.addEventListener(
        "input",
        updatePublicContactCharacterCount
    );


    updatePublicContactCharacterCount();
}



/* ============================================================
   PUBLIC WEBSITE
   LIGHT / DARK MODE
   ============================================================ */

const publicThemeToggle =
    document.getElementById(
        "themeToggle"
    );


function applyPublicTheme(theme) {

    const isDark =
        theme === "dark";


    document.body.classList.toggle(
        "dark-mode",
        isDark
    );


    document.documentElement.setAttribute(
        "data-public-theme",
        theme
    );


    if (publicThemeToggle) {

        publicThemeToggle.textContent =
            isDark
                ? "☼"
                : "☾";


        publicThemeToggle.setAttribute(
            "aria-label",
            isDark
                ? "Switch to light mode"
                : "Switch to dark mode"
        );


        publicThemeToggle.setAttribute(
            "title",
            isDark
                ? "Light mode"
                : "Dark mode"
        );

    }

}


/* ============================================================
   LOAD SAVED THEME
   ============================================================ */

const savedPublicTheme =
    localStorage.getItem(
        "orsc-public-theme"
    );


if (
    savedPublicTheme === "dark"
    ||
    savedPublicTheme === "light"
) {

    applyPublicTheme(
        savedPublicTheme
    );

}

else {

    applyPublicTheme(
        "light"
    );

}


/* ============================================================
   THEME BUTTON
   ============================================================ */

if (publicThemeToggle) {

    publicThemeToggle.addEventListener(
        "click",
        function () {

            const isDark =
                document.body.classList.contains(
                    "dark-mode"
                );


            const newTheme =
                isDark
                    ? "light"
                    : "dark";


            applyPublicTheme(
                newTheme
            );


            localStorage.setItem(
                "orsc-public-theme",
                newTheme
            );

        }
    );

}





/* ============================================================
   PUBLIC WEBSITE
   MOBILE NAVIGATION
   ============================================================ */

const publicMobileMenuButton =
    document.getElementById(
        "mobileMenuButton"
    );

const publicMobileMenu =
    document.getElementById(
        "mobileMenu"
    );


if (
    publicMobileMenuButton
    &&
    publicMobileMenu
) {

    publicMobileMenuButton.addEventListener(
        "click",
        function () {

            const isOpen =
                publicMobileMenu.classList.toggle(
                    "open"
                );


            publicMobileMenuButton.textContent =
                isOpen
                    ? "✕"
                    : "☰";


            publicMobileMenuButton.setAttribute(
                "aria-expanded",
                isOpen
                    ? "true"
                    : "false"
            );

        }
    );


    /* CLOSE AFTER CLICKING A LINK */

    publicMobileMenu
        .querySelectorAll("a")
        .forEach(
            function (link) {

                link.addEventListener(
                    "click",
                    function () {

                        publicMobileMenu
                            .classList
                            .remove("open");

                        publicMobileMenuButton
                            .textContent = "☰";

                        publicMobileMenuButton
                            .setAttribute(
                                "aria-expanded",
                                "false"
                            );

                    }
                );

            }
        );


    /* CLOSE IF SCREEN RETURNS TO DESKTOP */

    window.addEventListener(
        "resize",
        function () {

            if (
                window.innerWidth > 1050
            ) {

                publicMobileMenu
                    .classList
                    .remove("open");

                publicMobileMenuButton
                    .textContent = "☰";

                publicMobileMenuButton
                    .setAttribute(
                        "aria-expanded",
                        "false"
                    );

            }

        }
    );

}