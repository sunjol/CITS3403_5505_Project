/**
 * Password strength meter using jQuery.
 * Shows real-time feedback as user types their password.
 */
$(document).ready(function() {
    const $password = $('#password');
    const $strengthDiv = $('#password-strength');

    if (!$password.length || !$strengthDiv.length) {
        return; // Not on the signup page
    }

    function checkStrength(password) {
        let strength = 0;
        const checks = {
            length: password.length >= 8,
            longLength: password.length >= 12,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[^A-Za-z0-9]/.test(password)
        };

        // Score: 1 point per check (max 6)
        strength = Object.values(checks).filter(Boolean).length;

        if (password.length === 0) return { score: 0, label: '', class: '' };
        if (strength <= 2) return { score: strength, label: 'Weak', class: 'strength-weak' };
        if (strength <= 4) return { score: strength, label: 'Medium', class: 'strength-medium' };
        return { score: strength, label: 'Strong', class: 'strength-strong' };
    }

    $password.on('input', function() {
        const password = $(this).val();
        const result = checkStrength(password);

        if (password.length === 0) {
            $strengthDiv.html('').removeClass('strength-weak strength-medium strength-strong');
            return;
        }

        const percentage = (result.score / 6) * 100;
        $strengthDiv
            .removeClass('strength-weak strength-medium strength-strong')
            .addClass(result.class)
            .html(`
                <div class="strength-bar">
                    <div class="strength-bar-fill" style="width: ${percentage}%"></div>
                </div>
                <p class="strength-label mini">Password strength: <strong>${result.label}</strong></p>
            `);
    });
});