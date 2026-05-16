(function () {
  "use strict";

  var DEBOUNCE_MS = 250;

  function getStatusElement(form) {
    var statusId = form.querySelector(".live-search-input")?.getAttribute("aria-describedby");
    return statusId ? document.getElementById(statusId) : null;
  }

  function setStatus(form, message) {
    var status = getStatusElement(form);
    if (status) {
      status.textContent = message;
    }
  }

  function buildSearchParams(form) {
    var params = new URLSearchParams();
    Array.prototype.forEach.call(
      form.querySelectorAll("input[name], select[name]"),
      function (field) {
        if (!field.name || field.type === "submit") {
          return;
        }
        params.set(field.name, field.value);
      }
    );
    return params;
  }

  function bindConfirmHandlers(root) {
    root.querySelectorAll("[data-confirm-submit]").forEach(function (form) {
      if (form.dataset.confirmBound === "true") {
        return;
      }
      form.dataset.confirmBound = "true";
      form.addEventListener("submit", function (event) {
        var message = form.dataset.confirmMessage || "Are you sure?";
        if (!window.confirm(message)) {
          event.preventDefault();
        }
      });
    });
  }

  function runSearch(form) {
    var resultsTarget = form.dataset.resultsTarget;
    var searchUrl = form.dataset.searchUrl;
    if (!resultsTarget || !searchUrl) {
      return;
    }

    var resultsNode = document.querySelector(resultsTarget);
    if (!resultsNode) {
      return;
    }

    var requestId = (form._searchRequestId || 0) + 1;
    form._searchRequestId = requestId;
    resultsNode.classList.add("is-search-loading");
    setStatus(form, "Searching…");

    var url = searchUrl + "?" + buildSearchParams(form).toString();
    fetch(url, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        Accept: "application/json",
      },
      credentials: "same-origin",
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (result) {
        if (form._searchRequestId !== requestId) {
          return;
        }
        if (!result.ok || typeof result.data.html !== "string") {
          setStatus(form, "Could not load results. Please try again.");
          return;
        }

        resultsNode.innerHTML = result.data.html;
        bindConfirmHandlers(resultsNode);

        var count = result.data.count;
        var query = form.querySelector(".live-search-input")?.value.trim() || "";
        if (query) {
          setStatus(
            form,
            count === 1 ? "1 result for \"" + query + "\"" : count + " results for \"" + query + "\""
          );
        } else {
          setStatus(form, count === 1 ? "Showing 1 result" : "Showing " + count + " results");
        }
      })
      .catch(function () {
        if (form._searchRequestId === requestId) {
          setStatus(form, "Could not load results. Please try again.");
        }
      })
      .finally(function () {
        if (form._searchRequestId === requestId) {
          resultsNode.classList.remove("is-search-loading");
        }
      });
  }

  function scheduleSearch(form) {
    window.clearTimeout(form._searchTimer);
    form._searchTimer = window.setTimeout(function () {
      runSearch(form);
    }, DEBOUNCE_MS);
  }

  function initLiveSearchForm(form) {
    var searchInput = form.querySelector(".live-search-input");
    if (!searchInput) {
      return;
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      runSearch(form);
    });

    searchInput.addEventListener("input", function () {
      scheduleSearch(form);
    });

    form.querySelectorAll("select[name]").forEach(function (field) {
      field.addEventListener("change", function () {
        scheduleSearch(form);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form[data-live-search]").forEach(initLiveSearchForm);
  });
})();
