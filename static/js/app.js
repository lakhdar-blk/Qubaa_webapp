(function () {
    "use strict";

    /* Mobile navigation -------------------------------------------------- */
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("site-nav");

    function closeNav() {
        document.body.classList.remove("nav-open");
        if (toggle) {
            toggle.setAttribute("aria-expanded", "false");
        }
    }

    if (toggle && nav) {
        toggle.addEventListener("click", function () {
            var isOpen = document.body.classList.toggle("nav-open");
            toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });

        nav.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", closeNav);
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeNav();
            }
        });
    }

    /* Copy share link ---------------------------------------------------- */
    document.querySelectorAll("[data-copy-link]").forEach(function (button) {
        button.addEventListener("click", function () {
            var url = button.getAttribute("data-copy-url") || window.location.href;
            var label = button.querySelector("span");
            var copiedLabel = button.getAttribute("data-copied-label") || "Copied!";
            var originalLabel = label ? label.textContent : "";

            function showCopied() {
                if (label) {
                    label.textContent = copiedLabel;
                }
                button.classList.add("is-copied");
                window.setTimeout(function () {
                    if (label) {
                        label.textContent = originalLabel;
                    }
                    button.classList.remove("is-copied");
                }, 2200);
            }

            function fallbackCopy() {
                var field = document.createElement("textarea");
                field.value = url;
                field.setAttribute("readonly", "");
                field.style.position = "fixed";
                field.style.opacity = "0";
                document.body.appendChild(field);
                field.select();
                try {
                    document.execCommand("copy");
                    showCopied();
                } catch (error) {
                    window.prompt("", url);
                }
                document.body.removeChild(field);
            }

            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(url).then(showCopied, fallbackCopy);
            } else {
                fallbackCopy();
            }
        });
    });
})();
