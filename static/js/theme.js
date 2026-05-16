(function () {
  "use strict";

  var STORAGE_KEY = "promptshare-theme";
  var root = document.documentElement;

  function getStoredTheme() {
    var stored = localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : "dark";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    updateToggleButtons(theme);
  }

  function updateToggleButtons(theme) {
    document.querySelectorAll("[data-theme-option]").forEach(function (button) {
      var isActive = button.getAttribute("data-theme-option") === theme;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyTheme(getStoredTheme());

    document.querySelectorAll("[data-theme-option]").forEach(function (button) {
      button.addEventListener("click", function () {
        applyTheme(button.getAttribute("data-theme-option"));
      });
    });
  });
})();
