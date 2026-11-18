(function () {
    "use strict";

    /* Mobile sidebar ------------------------------------------------------ */
    var burger = document.querySelector(".dash-burger");
    var overlay = document.querySelector(".dash-overlay");

    function setNav(open) {
        document.body.classList.toggle("dash-nav-open", open);
        if (burger) {
            burger.setAttribute("aria-expanded", open ? "true" : "false");
        }
        if (overlay) {
            overlay.hidden = !open;
        }
    }

    if (burger) {
        burger.addEventListener("click", function () {
            setNav(!document.body.classList.contains("dash-nav-open"));
        });
    }

    if (overlay) {
        overlay.addEventListener("click", function () {
            setNav(false);
        });
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            setNav(false);
        }
    });

    /* Flash messages are rendered at the top of the page. After a redirect
       (deleting, publishing, bulk actions) ask the browser to start there so
       the confirmation is actually visible, especially on phones. Mobile
       browsers restore the scroll position late, so pin the page to the top
       once more after load. */
    if (document.querySelector(".flash-stack")) {
        if ("scrollRestoration" in window.history) {
            window.history.scrollRestoration = "manual";
        }

        var showFlash = function () {
            window.scrollTo(0, 0);
            document.documentElement.scrollTop = 0;
            document.body.scrollTop = 0;
        };

        showFlash();
        document.addEventListener("DOMContentLoaded", showFlash);
        window.addEventListener("load", showFlash);
        window.setTimeout(showFlash, 80);
    }

    /* Dismissible flash messages ------------------------------------------ */
    document.querySelectorAll(".flash-close").forEach(function (button) {
        button.addEventListener("click", function () {
            var flash = button.closest(".flash");
            if (flash) {
                flash.remove();
            }
        });
    });

    /* Select all rows ----------------------------------------------------- */
    var selectAll = document.querySelector("[data-select-all]");
    var rowChecks = function () {
        return Array.prototype.slice.call(
            document.querySelectorAll('input[name="selected"][form="bulk-form"]')
        );
    };

    if (selectAll) {
        selectAll.addEventListener("change", function () {
            rowChecks().forEach(function (checkbox) {
                checkbox.checked = selectAll.checked;
            });
        });

        document.addEventListener("change", function (event) {
            if (event.target && event.target.name === "selected") {
                var boxes = rowChecks();
                selectAll.checked =
                    boxes.length > 0 &&
                    boxes.every(function (box) {
                        return box.checked;
                    });
            }
        });
    }

    /* Confirmation dialogs ------------------------------------------------ */
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!window.confirm(form.getAttribute("data-confirm"))) {
                event.preventDefault();
                return;
            }

            // Slow phone networks invite a second tap: send the request once.
            var button = form.querySelector('button[type="submit"]');
            if (button) {
                button.disabled = true;
            }
        });
    });

    /* Image URL preview --------------------------------------------------- */
    var imageInput = document.querySelector("[data-image-input]");
    var preview = document.querySelector("[data-image-preview]");
    var previewImage = document.querySelector("[data-image-preview-img]");

    function updatePreview() {
        if (!imageInput || !preview || !previewImage) {
            return;
        }
        var url = imageInput.value.trim();
        if (!url) {
            preview.hidden = true;
            previewImage.removeAttribute("src");
            return;
        }
        previewImage.src = url;
        preview.hidden = false;
    }

    if (imageInput) {
        imageInput.addEventListener("input", updatePreview);
        previewImage.addEventListener("error", function () {
            preview.hidden = true;
        });
        updatePreview();
    }

    /* Title character counters -------------------------------------------- */
    document.querySelectorAll("[data-counter]").forEach(function (input) {
        var max = parseInt(input.getAttribute("data-counter"), 10);
        if (!max) {
            return;
        }
        var counter = document.createElement("span");
        counter.className = "field-count";
        input.insertAdjacentElement("afterend", counter);

        function refresh() {
            counter.textContent = input.value.length + " / " + max;
        }

        input.addEventListener("input", refresh);
        refresh();
    });
})();
