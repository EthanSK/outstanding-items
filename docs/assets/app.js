(function () {
  "use strict";

  var status = document.querySelector(".copy-status");
  var hideTimer = null;

  function announce(message) {
    if (!status) return;
    status.textContent = message;
    status.classList.add("is-visible");
    window.clearTimeout(hideTimer);
    hideTimer = window.setTimeout(function () {
      status.classList.remove("is-visible");
    }, 1800);
  }

  document.querySelectorAll("[data-copy-target]").forEach(function (button) {
    var target = document.getElementById(button.getAttribute("data-copy-target"));
    if (!target) return;

    button.addEventListener("click", function () {
      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        announce("Select the commands to copy them.");
        return;
      }

      navigator.clipboard.writeText(target.textContent).then(
        function () {
          button.textContent = "Copied";
          announce("Install commands copied.");
          window.setTimeout(function () {
            button.textContent = "Copy";
          }, 1800);
        },
        function () {
          announce("Copy failed. Select the commands instead.");
        }
      );
    });
  });
})();
