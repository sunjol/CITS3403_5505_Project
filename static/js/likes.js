(function () {
  "use strict";

  function getCsrfToken(form) {
    var input = form.querySelector('input[name="csrf_token"]');
    return input ? input.value : "";
  }

  function updateLikeButton(form, data) {
    var button = form.querySelector(".like-btn");
    var label = form.querySelector(".like-btn-label");
    var count = form.querySelector(".like-btn-count");
    if (!button || !label || !count) {
      return;
    }

    button.classList.toggle("is-liked", data.liked);
    button.setAttribute("aria-pressed", data.liked ? "true" : "false");
    label.textContent = data.liked ? "Liked" : "Like";
    count.textContent = String(data.like_count);
  }

  function showLikeToast(message, isError) {
    var toast = document.getElementById("like-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "like-toast";
      toast.className = "like-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.className = "like-toast like-toast--" + (isError ? "error" : "success");
    toast.hidden = false;

    window.clearTimeout(showLikeToast._timer);
    showLikeToast._timer = window.setTimeout(function () {
      toast.hidden = true;
      toast.textContent = "";
    }, 3000);
  }

  function sendLikeRequest(form, button) {
    if (form.dataset.loading === "true") {
      return;
    }

    form.dataset.loading = "true";
    if (button) {
      button.classList.add("is-loading");
    }

    fetch(form.action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        Accept: "application/json",
        "X-CSRFToken": getCsrfToken(form),
      },
      credentials: "same-origin",
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (result) {
        if (result.ok && result.data.success) {
          updateLikeButton(form, result.data);
          return;
        }
        showLikeToast(result.data.message || "Could not update like.", true);
      })
      .catch(function () {
        showLikeToast("Could not update like. Please try again.", true);
      })
      .finally(function () {
        form.dataset.loading = "false";
        if (button) {
          button.classList.remove("is-loading");
        }
      });
  }

  function prepareLikeForm(form) {
    var button = form.querySelector(".like-btn");
    if (button && button.type !== "button") {
      button.type = "button";
    }
    return button;
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".like-btn");
    if (!button) {
      return;
    }

    var form = button.closest("form.like-form");
    if (!form) {
      return;
    }

    event.preventDefault();
    prepareLikeForm(form);
    sendLikeRequest(form, button);
  });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form.like-form").forEach(prepareLikeForm);
  });
})();
