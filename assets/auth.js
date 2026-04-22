/* ==========================================================
   PromptShare - Authentication Client-Side Validation
   Handles signup and login form validation before submission
   ========================================================== */

(function () {
  'use strict';

  // Regular expressions for validation
  var USERNAME_RE = /^[A-Za-z0-9_]{3,20}$/;
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  /**
   * Show an error message below a form field.
   */
  function showError(input, message) {
    clearError(input);
    input.classList.add('field-error');

    var errorEl = document.createElement('p');
    errorEl.className = 'mini field-error-text';
    errorEl.textContent = message;
    errorEl.setAttribute('data-error-for', input.id);

    // Insert after the input (or its parent wrapper div)
    var parent = input.parentElement;
    parent.appendChild(errorEl);
  }

  /**
   * Clear the error message for a field.
   */
  function clearError(input) {
    input.classList.remove('field-error');
    var parent = input.parentElement;
    var existing = parent.querySelector('[data-error-for="' + input.id + '"]');
    if (existing) {
      existing.remove();
    }
  }

  /**
   * Validate a single field. Returns true if valid.
   */
  function validateUsername(input) {
    var value = input.value.trim();
    if (!value) {
      showError(input, 'Username is required.');
      return false;
    }
    if (!USERNAME_RE.test(value)) {
      showError(input, 'Use 3-20 letters, numbers, or underscores.');
      return false;
    }
    clearError(input);
    return true;
  }

  function validateEmail(input) {
    var value = input.value.trim();
    if (!value) {
      showError(input, 'Email is required.');
      return false;
    }
    if (!EMAIL_RE.test(value)) {
      showError(input, 'Please enter a valid email address.');
      return false;
    }
    clearError(input);
    return true;
  }

  function validatePassword(input) {
    var value = input.value;
    if (value.length < 8) {
      showError(input, 'Password must be at least 8 characters.');
      return false;
    }
    if (!/[A-Za-z]/.test(value) || !/[0-9]/.test(value)) {
      showError(input, 'Include both letters and numbers.');
      return false;
    }
    clearError(input);
    return true;
  }

  function validateConfirmPassword(confirmInput, passwordInput) {
    if (!confirmInput.value) {
      showError(confirmInput, 'Please confirm your password.');
      return false;
    }
    if (confirmInput.value !== passwordInput.value) {
      showError(confirmInput, 'Passwords do not match.');
      return false;
    }
    clearError(confirmInput);
    return true;
  }

  // Wire up the signup form
  var signupForm = document.getElementById('signup-form');
  if (signupForm) {
    var username = document.getElementById('username');
    var email = document.getElementById('email');
    var password = document.getElementById('password');
    var confirmPassword = document.getElementById('confirm-password');

    // Validate on blur (when user leaves the field)
    username.addEventListener('blur', function () { validateUsername(username); });
    email.addEventListener('blur', function () { validateEmail(email); });
    password.addEventListener('blur', function () { validatePassword(password); });
    confirmPassword.addEventListener('input', function () {
      validateConfirmPassword(confirmPassword, password);
    });

    // Validate all fields on submit
    signupForm.addEventListener('submit', function (e) {
      var results = [
        validateUsername(username),
        validateEmail(email),
        validatePassword(password),
        validateConfirmPassword(confirmPassword, password)
      ];

      if (results.indexOf(false) !== -1) {
        e.preventDefault();
        var firstError = signupForm.querySelector('.field-error');
        if (firstError) firstError.focus();
      }
    });
  }

})();
