const attachmentInput = document.getElementById("attachmentInput");

if (attachmentInput) {

    const allowedExtensions = [
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        "txt",
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
        "mp4",
        "mov",
        "avi",
        "mkv",
        "webm"
    ];

    attachmentInput.addEventListener("change", function () {

        const file = attachmentInput.files[0];

        if (!file) {
            return;
        }

        const extension =
            file.name
                .split(".")
                .pop()
                .toLowerCase();

        if (!allowedExtensions.includes(extension)) {

            const attachmentError = document.getElementById("attachmentError");
            
            if (!allowedExtensions.includes(extension)) {
                attachmentError.textContent =
                "Ce type de fichier n'est pas autorisé.";
                
                attachmentError.classList.add("show");
                
                attachmentInput.value = "";
                
                return;
            }
            
            attachmentError.textContent = "";
            
            attachmentError.classList.remove("show");
            
            attachmentInput.value = "";

        }

    });

}



/* ========================================
   MEMBERS SEARCH + FILTERS
   ======================================== */

const membersSearch =
    document.getElementById("membersSearch");

const departmentFilter =
    document.getElementById("departmentFilter");

const roleFilter =
    document.getElementById("roleFilter");

const statusFilter =
    document.getElementById("statusFilter");

const termFilter =
    document.getElementById("termFilter");

const memberRows =
    document.querySelectorAll(".member-row");

const membersNoResults =
    document.getElementById("membersNoResults");


function applyMemberFilters() {

    const searchValue =
        membersSearch
            ? membersSearch.value
                .trim()
                .toLowerCase()
            : "";


    const departmentValue =
        departmentFilter
            ? departmentFilter.value
            : "all";


    const roleValue =
        roleFilter
            ? roleFilter.value
            : "all";


    const statusValue =
        statusFilter
            ? statusFilter.value
            : "all";


    const termValue =
        termFilter
            ? termFilter.value
            : "all";


    let visibleMembers = 0;


    memberRows.forEach(function (member) {

        const searchableText =
            member.dataset.search
                .toLowerCase();


        const matchesSearch =
            searchableText.includes(
                searchValue
            );


        const matchesDepartment =
            departmentValue === "all"
            ||
            member.dataset.department
            === departmentValue;


        const matchesRole =
            roleValue === "all"
            ||
            member.dataset.role
            === roleValue;


        const matchesStatus =
            statusValue === "all"
            ||
            member.dataset.status
            === statusValue;


        const matchesTerm =
            termValue === "all"
            ||
            member.dataset.term
            === termValue;


        if (
            matchesSearch
            &&
            matchesDepartment
            &&
            matchesRole
            &&
            matchesStatus
            &&
            matchesTerm
        ) {

            member.style.display = "";
            visibleMembers++;

        } else {

            member.style.display = "none";

        }

    });


    if (membersNoResults) {

        if (visibleMembers === 0) {

            membersNoResults.style.display =
                "block";

        } else {

            membersNoResults.style.display =
                "none";

        }

    }

}


if (membersSearch) {

    membersSearch.addEventListener(
        "input",
        applyMemberFilters
    );

}


if (departmentFilter) {

    departmentFilter.addEventListener(
        "change",
        applyMemberFilters
    );

}


if (roleFilter) {

    roleFilter.addEventListener(
        "change",
        applyMemberFilters
    );

}


if (statusFilter) {

    statusFilter.addEventListener(
        "change",
        applyMemberFilters
    );

}


if (termFilter) {

    termFilter.addEventListener(
        "change",
        applyMemberFilters
    );

}




/* =========================================================
   PROFILE PHOTO CROPPER
========================================================= */

const profilePhotoInput =
    document.getElementById("profile_photo");

const profileCropModal =
    document.getElementById("profileCropModal");

const profileCropViewport =
    document.getElementById("profileCropViewport");

const profileCropImage =
    document.getElementById("profileCropImage");

const profileCropZoom =
    document.getElementById("profileCropZoom");

const profileCropCancel =
    document.getElementById("profileCropCancel");

const profileCropClose =
    document.getElementById("profileCropClose");

const profileCropBackdrop =
    document.getElementById("profileCropBackdrop");

const profileCropApply =
    document.getElementById("profileCropApply");

const profileCropCanvas =
    document.getElementById("profileCropCanvas");

const profilePhotoPreviewImage =
    document.getElementById(
        "profilePhotoPreviewImage"
    );

const profilePhotoPreviewInitials =
    document.getElementById(
        "profilePhotoPreviewInitials"
    );

const profilePhotoStatus =
    document.getElementById(
        "profilePhotoStatus"
    );


if (
    profilePhotoInput
    &&
    profileCropModal
    &&
    profileCropViewport
    &&
    profileCropImage
    &&
    profileCropZoom
    &&
    profileCropCanvas
) {

    let imageURL = null;

    let baseScale = 1;
    let zoom = 1;

    let offsetX = 0;
    let offsetY = 0;

    let isDragging = false;

    let dragStartX = 0;
    let dragStartY = 0;

    let startOffsetX = 0;
    let startOffsetY = 0;


    /* =========================================
       OPEN CROPPER
    ========================================== */

    profilePhotoInput.addEventListener(
        "change",
        function () {

            const file =
                profilePhotoInput.files[0];

            if (!file) {
                return;
            }


            /* File must be an image */

            if (
                !file.type.startsWith("image/")
            ) {

                profilePhotoInput.value = "";

                return;
            }


            /* Remove old temporary URL */

            if (imageURL) {

                URL.revokeObjectURL(
                    imageURL
                );

            }


            imageURL =
                URL.createObjectURL(
                    file
                );


            profileCropImage.onload =
                function () {

                    openProfileCropper();

                };


            profileCropImage.src =
                imageURL;

        }
    );


    /* =========================================
       OPEN MODAL
    ========================================== */

    function openProfileCropper() {

        profileCropModal.hidden =
            false;

        document.body.style.overflow =
            "hidden";


        zoom = 1;

        offsetX = 0;
        offsetY = 0;

        profileCropZoom.value =
            "1";


        /*
        Wait until the modal is visible
        before calculating its size.
        */

        requestAnimationFrame(
            function () {

                calculateBaseScale();

                updateCropImage();

            }
        );

    }


    /* =========================================
       CALCULATE MINIMUM SCALE
    ========================================== */

    function calculateBaseScale() {

        const viewportWidth =
            profileCropViewport.clientWidth;

        const viewportHeight =
            profileCropViewport.clientHeight;


        const imageWidth =
            profileCropImage.naturalWidth;

        const imageHeight =
            profileCropImage.naturalHeight;


        if (
            !viewportWidth
            ||
            !viewportHeight
            ||
            !imageWidth
            ||
            !imageHeight
        ) {
            return;
        }


        /*
        Cover the entire crop area.
        */

        baseScale =
            Math.max(
                viewportWidth / imageWidth,
                viewportHeight / imageHeight
            );

    }


    /* =========================================
       UPDATE IMAGE POSITION
    ========================================== */

    function updateCropImage() {

        const scale =
            baseScale * zoom;


        const displayedWidth =
            profileCropImage.naturalWidth
            * scale;

        const displayedHeight =
            profileCropImage.naturalHeight
            * scale;


        const viewportWidth =
            profileCropViewport.clientWidth;

        const viewportHeight =
            profileCropViewport.clientHeight;


        /*
        Prevent empty areas from appearing.
        */

        const maxX =
            Math.max(
                0,
                (
                    displayedWidth
                    - viewportWidth
                ) / 2
            );

        const maxY =
            Math.max(
                0,
                (
                    displayedHeight
                    - viewportHeight
                ) / 2
            );


        offsetX =
            Math.max(
                -maxX,
                Math.min(
                    maxX,
                    offsetX
                )
            );


        offsetY =
            Math.max(
                -maxY,
                Math.min(
                    maxY,
                    offsetY
                )
            );


        profileCropImage.style.width =
            displayedWidth + "px";

        profileCropImage.style.height =
            displayedHeight + "px";


        profileCropImage.style.position =
            "absolute";

        profileCropImage.style.left =
            "50%";

        profileCropImage.style.top =
            "50%";


        profileCropImage.style.transform =
            `
            translate(-50%, -50%)
            translate(
                ${offsetX}px,
                ${offsetY}px
            )
            `;

    }


    /* =========================================
       ZOOM
    ========================================== */

    profileCropZoom.addEventListener(
        "input",
        function () {

            zoom =
                parseFloat(
                    profileCropZoom.value
                );

            updateCropImage();

        }
    );


    /* =========================================
       START DRAG
    ========================================== */

    function startDrag(
        clientX,
        clientY
    ) {

        isDragging = true;

        dragStartX =
            clientX;

        dragStartY =
            clientY;

        startOffsetX =
            offsetX;

        startOffsetY =
            offsetY;

        profileCropViewport.classList.add(
            "dragging"
        );

    }


    /* =========================================
       MOVE IMAGE
    ========================================== */

    function moveDrag(
        clientX,
        clientY
    ) {

        if (!isDragging) {
            return;
        }


        offsetX =
            startOffsetX
            +
            (
                clientX
                - dragStartX
            );


        offsetY =
            startOffsetY
            +
            (
                clientY
                - dragStartY
            );


        updateCropImage();

    }


    /* =========================================
       END DRAG
    ========================================== */

    function endDrag() {

        isDragging = false;

        profileCropViewport
            .classList
            .remove(
                "dragging"
            );

    }


    /* =========================================
       MOUSE EVENTS
    ========================================== */

    profileCropViewport.addEventListener(
        "mousedown",
        function (event) {

            event.preventDefault();

            startDrag(
                event.clientX,
                event.clientY
            );

        }
    );


    window.addEventListener(
        "mousemove",
        function (event) {

            moveDrag(
                event.clientX,
                event.clientY
            );

        }
    );


    window.addEventListener(
        "mouseup",
        endDrag
    );


    /* =========================================
       TOUCH EVENTS
    ========================================== */

    profileCropViewport.addEventListener(
        "touchstart",
        function (event) {

            if (
                event.touches.length !== 1
            ) {
                return;
            }


            const touch =
                event.touches[0];


            startDrag(
                touch.clientX,
                touch.clientY
            );

        },
        {
            passive: true
        }
    );


    profileCropViewport.addEventListener(
        "touchmove",
        function (event) {

            if (
                event.touches.length !== 1
            ) {
                return;
            }


            const touch =
                event.touches[0];


            moveDrag(
                touch.clientX,
                touch.clientY
            );

        },
        {
            passive: true
        }
    );


    profileCropViewport.addEventListener(
        "touchend",
        endDrag
    );


    /* =========================================
       CANCEL
    ========================================== */

    function cancelProfileCrop() {

        profileCropModal.hidden =
            true;

        document.body.style.overflow =
            "";

        profilePhotoInput.value =
            "";

    }


    if (profileCropCancel) {

        profileCropCancel.addEventListener(
            "click",
            cancelProfileCrop
        );

    }


    if (profileCropClose) {

        profileCropClose.addEventListener(
            "click",
            cancelProfileCrop
        );

    }


    if (profileCropBackdrop) {

        profileCropBackdrop.addEventListener(
            "click",
            cancelProfileCrop
        );

    }


    /* =========================================
       APPLY CROP
    ========================================== */

    if (profileCropApply) {

        profileCropApply.addEventListener(
            "click",
            function () {

                const viewportWidth =
                    profileCropViewport.clientWidth;

                const viewportHeight =
                    profileCropViewport.clientHeight;


                const scale =
                    baseScale * zoom;


                const displayedWidth =
                    profileCropImage.naturalWidth
                    * scale;

                const displayedHeight =
                    profileCropImage.naturalHeight
                    * scale;


                /*
                Position of displayed image
                inside crop viewport.
                */

                const imageLeft =
                    (
                        viewportWidth
                        - displayedWidth
                    ) / 2
                    +
                    offsetX;


                const imageTop =
                    (
                        viewportHeight
                        - displayedHeight
                    ) / 2
                    +
                    offsetY;


                /*
                Convert viewport coordinates
                back to original image pixels.
                */

                const sourceX =
                    Math.max(
                        0,
                        -imageLeft / scale
                    );


                const sourceY =
                    Math.max(
                        0,
                        -imageTop / scale
                    );


                const sourceWidth =
                    viewportWidth / scale;


                const sourceHeight =
                    viewportHeight / scale;


                /*
                Final image is square.
                */

                const canvasSize =
                    500;


                profileCropCanvas.width =
                    canvasSize;

                profileCropCanvas.height =
                    canvasSize;


                const context =
                    profileCropCanvas
                        .getContext("2d");


                context.clearRect(
                    0,
                    0,
                    canvasSize,
                    canvasSize
                );


                context.drawImage(
                    profileCropImage,

                    sourceX,
                    sourceY,

                    sourceWidth,
                    sourceHeight,

                    0,
                    0,

                    canvasSize,
                    canvasSize
                );


                /* =================================
                   CREATE NEW IMAGE FILE
                ================================= */

                profileCropCanvas.toBlob(
                    function (blob) {

                        if (!blob) {
                            return;
                        }


                        const croppedFile =
                            new File(
                                [
                                    blob
                                ],

                                "profile-photo.webp",

                                {
                                    type:
                                        "image/webp"
                                }
                            );


                        /*
                        Replace original file
                        inside file input.
                        */

                        const dataTransfer =
                            new DataTransfer();


                        dataTransfer.items.add(
                            croppedFile
                        );


                        profilePhotoInput.files =
                            dataTransfer.files;


                        /* =============================
                           UPDATE PREVIEW
                        ============================= */

                        const previewURL =
                            URL.createObjectURL(
                                blob
                            );


                        if (
                            profilePhotoPreviewImage
                        ) {

                            profilePhotoPreviewImage.src =
                                previewURL;

                            profilePhotoPreviewImage.hidden =
                                false;

                        }


                        if (
                            profilePhotoPreviewInitials
                        ) {

                            profilePhotoPreviewInitials.hidden =
                                true;

                        }


                        if (
                            profilePhotoStatus
                        ) {

                            profilePhotoStatus.textContent =
                                "New photo ready to save.";

                        }


                        /* =============================
                           CLOSE MODAL
                        ============================= */

                        profileCropModal.hidden =
                            true;

                        document.body.style.overflow =
                            "";

                    },

                    "image/webp",

                    0.92
                );

            }
        );

    }


    /* =========================================
       ESCAPE KEY
    ========================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
                &&
                !profileCropModal.hidden
            ) {

                cancelProfileCrop();

            }

        }
    );


    /* =========================================
       RESIZE
    ========================================== */

    window.addEventListener(
        "resize",
        function () {

            if (
                profileCropModal.hidden
            ) {
                return;
            }


            calculateBaseScale();

            updateCropImage();

        }
    );

}




/* ========================================
   ANNOUNCEMENTS AUTO FILTERS
   ======================================== */

const announcementsFiltersForm =
    document.getElementById(
        "announcementsFiltersForm"
    );

if (announcementsFiltersForm) {

    const announcementSearch =
        document.getElementById("q");

    const announcementVisibility =
        document.getElementById("visibility");

    const announcementStatus =
        document.getElementById("status");

    const announcementRead =
        document.getElementById("read");


    let announcementSearchTimer;


    /* ========================================
       SELECT FILTERS
       ======================================== */

    [
        announcementVisibility,
        announcementStatus,
        announcementRead
    ].forEach(function (filter) {

        if (!filter) {
            return;
        }

        filter.addEventListener(
            "change",
            function () {

                announcementsFiltersForm
                    .requestSubmit();

            }
        );

    });


    /* ========================================
       SEARCH
       ======================================== */

    if (announcementSearch) {

        announcementSearch.addEventListener(
            "input",
            function () {

                clearTimeout(
                    announcementSearchTimer
                );


                announcementSearchTimer =
                    setTimeout(
                        function () {

                            announcementsFiltersForm
                                .requestSubmit();

                        },
                        350
                    );

            }
        );

    }

}




const trainingMediaFile =
    document.getElementById("media_file");

const trainingFileName =
    document.getElementById("trainingFileName");


if (trainingMediaFile && trainingFileName) {

    trainingMediaFile.addEventListener(
        "change",
        function () {

            if (
                trainingMediaFile.files &&
                trainingMediaFile.files.length > 0
            ) {

                trainingFileName.textContent =
                    trainingMediaFile.files[0].name;

            } else {

                trainingFileName.textContent =
                    "No file chosen";

            }

        }
    );

}




// ============================================================
// TRAINING MEDIA VIEWER
// ============================================================

const trainingMediaOpenButtons =
    document.querySelectorAll(".training-media-open");

const trainingMediaModal =
    document.getElementById("trainingMediaModal");

const trainingMediaModalViewer =
    document.getElementById("trainingMediaModalViewer");

const trainingMediaModalCaption =
    document.getElementById("trainingMediaModalCaption");

const trainingMediaModalDownload =
    document.getElementById("trainingMediaModalDownload");

const trainingMediaModalClose =
    document.getElementById("trainingMediaModalClose");

const trainingMediaModalOverlay =
    document.getElementById("trainingMediaModalOverlay");


if (
    trainingMediaOpenButtons.length &&
    trainingMediaModal
) {

    function openTrainingMediaModal(button) {

        const hiddenData =
            button.querySelector(
                ".training-media-hidden-data"
            );

        if (!hiddenData) {
            return;
        }


        const mediaType =
            hiddenData.querySelector(
                ".training-media-modal-type"
            )?.textContent.trim();


        const mediaUrl =
            hiddenData.querySelector(
                ".training-media-modal-url"
            )?.textContent.trim();


        const downloadUrl =
            hiddenData.querySelector(
                ".training-media-modal-download"
            )?.textContent.trim();


        const caption =
            hiddenData.querySelector(
                ".training-media-modal-caption"
            )?.textContent.trim();


        // Remove previous media
        trainingMediaModalViewer.innerHTML = "";


        // ====================================================
        // IMAGE
        // ====================================================

        if (mediaType === "image") {

            const image = document.createElement("img");

            image.src = mediaUrl;
            image.alt = caption || "Training photo";

            trainingMediaModalViewer.appendChild(
                image
            );

        }


        // ====================================================
        // VIDEO
        // ====================================================

        else if (mediaType === "video") {

            const video =
                document.createElement("video");

            video.src = mediaUrl;

            video.controls = true;
            video.autoplay = false;
            video.preload = "metadata";

            trainingMediaModalViewer.appendChild(
                video
            );

        }


        // ====================================================
        // CAPTION
        // ====================================================

        if (caption) {

            trainingMediaModalCaption.textContent =
                caption;

            trainingMediaModalCaption.style.display =
                "";

        } else {

            trainingMediaModalCaption.textContent =
                "No caption.";

            trainingMediaModalCaption.style.display =
                "";

        }


        // ====================================================
        // DOWNLOAD
        // ====================================================

        trainingMediaModalDownload.href =
            downloadUrl;


        // ====================================================
        // OPEN
        // ====================================================

        trainingMediaModal.classList.add("open");

        trainingMediaModal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.style.overflow =
            "hidden";

        document.body.classList.add(
            "training-media-modal-open"
        );
    }


    function closeTrainingMediaModal() {

        // Stop video if one is playing
        const video =
            trainingMediaModalViewer.querySelector(
                "video"
            );

        if (video) {

            video.pause();

            video.currentTime = 0;
        }


        trainingMediaModal.classList.remove(
            "open"
        );

        trainingMediaModal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.style.overflow =
            "";

        document.body.classList.remove(
            "training-media-modal-open"
        );


        // Clean viewer
        trainingMediaModalViewer.innerHTML =
            "";
    }


    // ========================================================
    // OPEN MEDIA
    // ========================================================

    trainingMediaOpenButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    openTrainingMediaModal(
                        button
                    );

                }
            );

        }
    );


    // ========================================================
    // CLOSE BUTTON
    // ========================================================

    if (trainingMediaModalClose) {

        trainingMediaModalClose.addEventListener(
            "click",
            closeTrainingMediaModal
        );

    }


    // ========================================================
    // CLICK ON OVERLAY
    // ========================================================

    if (trainingMediaModalOverlay) {

        trainingMediaModalOverlay.addEventListener(
            "click",
            closeTrainingMediaModal
        );

    }


    // ========================================================
    // ESCAPE KEY
    // ========================================================

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
                &&
                trainingMediaModal.classList.contains(
                    "open"
                )
            ) {

                closeTrainingMediaModal();

            }

        }
    );

}





/* ============================================================
   CMS GLOBAL SEARCH
   ============================================================ */

const cmsGlobalSearch =
    document.getElementById(
        "cmsGlobalSearch"
    );

const cmsGlobalSearchResults =
    document.getElementById(
        "cmsGlobalSearchResults"
    );


if (
    cmsGlobalSearch
    &&
    cmsGlobalSearchResults
) {

    const cmsSearchPages =
        Array.from(
            document.querySelectorAll(
                ".sidebar-nav .nav-item"
            )
        )
        .map(
            function (link) {

                const label =
                    link.textContent
                        .trim()
                        .replace(
                            /\s+/g,
                            " "
                        );

                const iconElement =
                    link.querySelector(
                        ".nav-icon"
                    );

                return {

                    label: label,

                    href:
                        link.href,

                    icon:
                        iconElement
                            ? iconElement
                                .textContent
                                .trim()
                            : "→"

                };

            }
        );


    function closeCmsSearch() {

        cmsGlobalSearchResults.hidden =
            true;

        cmsGlobalSearchResults.innerHTML =
            "";

        cmsGlobalSearch.setAttribute(
            "aria-expanded",
            "false"
        );

    }


    function renderCmsSearch() {

        const query =
            cmsGlobalSearch.value
                .trim()
                .toLowerCase();


        cmsGlobalSearchResults.innerHTML =
            "";


        if (!query) {

            closeCmsSearch();

            return;

        }


        const matches =
            cmsSearchPages
                .filter(
                    function (page) {

                        return page.label
                            .toLowerCase()
                            .includes(
                                query
                            );

                    }
                )
                .slice(
                    0,
                    8
                );


        cmsGlobalSearchResults.hidden =
            false;

        cmsGlobalSearch.setAttribute(
            "aria-expanded",
            "true"
        );


        if (
            matches.length === 0
        ) {

            const empty =
                document.createElement(
                    "div"
                );

            empty.className =
                "cms-global-search-empty";

            empty.textContent =
                "No matching page found.";

            cmsGlobalSearchResults
                .appendChild(
                    empty
                );

            return;

        }


        matches.forEach(
            function (page) {

                const result =
                    document.createElement(
                        "a"
                    );

                result.className =
                    "cms-global-search-result";

                result.href =
                    page.href;


                const icon =
                    document.createElement(
                        "span"
                    );

                icon.className =
                    "cms-global-search-result-icon";

                icon.textContent =
                    page.icon;


                const text =
                    document.createElement(
                        "span"
                    );

                text.className =
                    "cms-global-search-result-text";

                text.textContent =
                    page.label;


                const arrow =
                    document.createElement(
                        "span"
                    );

                arrow.className =
                    "cms-global-search-result-arrow";

                arrow.textContent =
                    "→";


                result.appendChild(
                    icon
                );

                result.appendChild(
                    text
                );

                result.appendChild(
                    arrow
                );


                cmsGlobalSearchResults
                    .appendChild(
                        result
                    );

            }
        );

    }


    cmsGlobalSearch.addEventListener(
        "input",
        renderCmsSearch
    );


    cmsGlobalSearch.addEventListener(
        "focus",
        function () {

            if (
                cmsGlobalSearch.value
                    .trim()
            ) {

                renderCmsSearch();

            }

        }
    );


    cmsGlobalSearch.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
            ) {

                closeCmsSearch();

                cmsGlobalSearch.blur();

            }


            if (
                event.key === "Enter"
            ) {

                const firstResult =
                    cmsGlobalSearchResults
                        .querySelector(
                            ".cms-global-search-result"
                        );


                if (firstResult) {

                    event.preventDefault();

                    window.location.href =
                        firstResult.href;

                }

            }

        }
    );


    document.addEventListener(
        "click",
        function (event) {

            if (
                !event.target.closest(
                    ".cms-global-search"
                )
            ) {

                closeCmsSearch();

            }

        }
    );

}









/* ============================================================
   CUSTOM CMS FILTER DROPDOWNS
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const customFilters =
            document.querySelectorAll(
                ".cms-filter-select"
            );


        function closeCustomFilters(
            exceptFilter = null
        ) {

            customFilters.forEach(
                function (filter) {

                    if (
                        filter === exceptFilter
                    ) {
                        return;
                    }


                    const trigger =
                        filter.querySelector(
                            ".cms-filter-trigger"
                        );

                    const menu =
                        filter.querySelector(
                            ".cms-filter-menu"
                        );


                    filter.classList.remove(
                        "open"
                    );


                    if (menu) {

                        menu.hidden = true;

                    }


                    if (trigger) {

                        trigger.setAttribute(
                            "aria-expanded",
                            "false"
                        );

                    }

                }
            );

        }



        customFilters.forEach(
            function (filter) {

                const nativeSelect =
                    filter.querySelector(
                        ".cms-native-filter"
                    );

                const trigger =
                    filter.querySelector(
                        ".cms-filter-trigger"
                    );

                const triggerText =
                    filter.querySelector(
                        ".cms-filter-trigger-text"
                    );

                const menu =
                    filter.querySelector(
                        ".cms-filter-menu"
                    );

                const options =
                    filter.querySelectorAll(
                        ".cms-filter-option"
                    );


                if (
                    !nativeSelect
                    ||
                    !trigger
                    ||
                    !triggerText
                    ||
                    !menu
                ) {
                    return;
                }



                /* ========================================
                   OPEN FILTER
                   ======================================== */

                trigger.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();

                        event.stopPropagation();


                        const wasOpen =
                            filter.classList.contains(
                                "open"
                            );


                        closeCustomFilters(
                            filter
                        );


                        if (wasOpen) {

                            filter.classList.remove(
                                "open"
                            );

                            menu.hidden = true;

                            trigger.setAttribute(
                                "aria-expanded",
                                "false"
                            );

                        } else {

                            filter.classList.add(
                                "open"
                            );

                            menu.hidden = false;

                            trigger.setAttribute(
                                "aria-expanded",
                                "true"
                            );

                        }

                    }
                );



                /* ========================================
                   SELECT OPTION
                   ======================================== */

                options.forEach(
                    function (option) {

                        option.addEventListener(
                            "click",
                            function (event) {

                                event.preventDefault();

                                event.stopPropagation();


                                const value =
                                    option.dataset.value;


                                nativeSelect.value =
                                    value;


                                triggerText.textContent =
                                    option.textContent
                                        .trim();


                                options.forEach(
                                    function (item) {

                                        item.classList.remove(
                                            "active"
                                        );

                                    }
                                );


                                option.classList.add(
                                    "active"
                                );


                                filter.classList.remove(
                                    "open"
                                );

                                menu.hidden = true;


                                trigger.setAttribute(
                                    "aria-expanded",
                                    "false"
                                );


                                nativeSelect.dispatchEvent(
                                    new Event(
                                        "change",
                                        {
                                            bubbles: true
                                        }
                                    )
                                );

                            }
                        );

                    }
                );

            }
        );



        /* ========================================
           CLICK OUTSIDE
           ======================================== */

        document.addEventListener(
            "click",
            function () {

                closeCustomFilters();

            }
        );



        /* ========================================
           ESCAPE KEY
           ======================================== */

        document.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Escape"
                ) {

                    closeCustomFilters();

                }

            }
        );

    }
);











/* ============================================================
   CMS CUSTOM FILE PICKERS
   ============================================================ */

document
    .querySelectorAll(
        ".cms-file-picker"
    )
    .forEach(
        function (picker) {

            const input =
                picker.querySelector(
                    ".cms-file-input"
                );

            const fileName =
                picker.querySelector(
                    ".cms-file-name"
                );


            if (
                !input
                ||
                !fileName
            ) {
                return;
            }


            input.addEventListener(
                "change",
                function () {

                    if (
                        input.files
                        &&
                        input.files.length > 0
                    ) {

                        fileName.textContent =
                            input.files[0].name;


                        picker.classList.add(
                            "has-file"
                        );

                    } else {

                        fileName.textContent =
                            "No file selected";


                        picker.classList.remove(
                            "has-file"
                        );

                    }

                }
            );

        }
    );












    /* =========================================================
   MOBILE SIDEBAR
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const mobileMenuToggle =
            document.querySelector(
                "[data-mobile-menu-toggle]"
            );


        const mobileSidebarOverlay =
            document.querySelector(
                "[data-mobile-sidebar-overlay]"
            );


        const sidebar =
            document.querySelector(
                ".sidebar"
            );


        if (
            !mobileMenuToggle
            ||
            !mobileSidebarOverlay
            ||
            !sidebar
        ) {
            return;
        }


        /* =========================================
           OPEN
           ========================================= */

        function openMobileSidebar() {

            document.body.classList.add(
                "sidebar-open"
            );


            mobileMenuToggle.setAttribute(
                "aria-expanded",
                "true"
            );

        }



        /* =========================================
           CLOSE
           ========================================= */

        function closeMobileSidebar() {

            document.body.classList.remove(
                "sidebar-open"
            );


            mobileMenuToggle.setAttribute(
                "aria-expanded",
                "false"
            );

        }



        /* =========================================
           TOGGLE
           ========================================= */

        mobileMenuToggle.addEventListener(
            "click",
            function () {

                if (
                    document.body.classList.contains(
                        "sidebar-open"
                    )
                ) {

                    closeMobileSidebar();

                } else {

                    openMobileSidebar();

                }

            }
        );



        /* =========================================
           CLICK OUTSIDE
           ========================================= */

        mobileSidebarOverlay.addEventListener(
            "click",
            closeMobileSidebar
        );



        /* =========================================
           CLOSE AFTER NAVIGATION
           ========================================= */

        sidebar
            .querySelectorAll(
                ".nav-item"
            )
            .forEach(
                function (link) {

                    link.addEventListener(
                        "click",
                        function () {

                            if (
                                window.innerWidth
                                <= 767
                            ) {

                                closeMobileSidebar();

                            }

                        }
                    );

                }
            );



        /* =========================================
           ESCAPE
           ========================================= */

        document.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Escape"
                    &&
                    document.body.classList.contains(
                        "sidebar-open"
                    )
                ) {

                    closeMobileSidebar();

                }

            }
        );



        /* =========================================
           RESIZE BACK TO PC / TABLET
           ========================================= */

        window.addEventListener(
            "resize",
            function () {

                if (
                    window.innerWidth > 767
                ) {

                    closeMobileSidebar();

                }

            }
        );

    }
);