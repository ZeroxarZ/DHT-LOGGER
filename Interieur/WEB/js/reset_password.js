const passwordInput = document.getElementById('new_password');
const bar = document.getElementById('password-strength-bar-inner');
const text = document.getElementById('password-strength-text');

function checkStrength(pw) {
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[a-z]/.test(pw)) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/\d/.test(pw)) score++;
    if (/[^a-zA-Z0-9]/.test(pw)) score++;
    return score;
}

passwordInput.addEventListener('input', function() {
    const value = passwordInput.value;
    const score = checkStrength(value);

    let width = "0%";
    let color = "red";
    let label = "Trop faible";

    if (score <= 1) {
        width = "20%";
        color = "red";
        label = "Très faible";
    } else if (score === 2) {
        width = "40%";
        color = "orange";
        label = "Faible";
    } else if (score === 3) {
        width = "60%";
        color = "#e6c300";
        label = "Moyen";
    } else if (score === 4) {
        width = "80%";
        color = "#4caf50";
        label = "Robuste";
    } else if (score === 5) {
        width = "100%";
        color = "#2e7d32";
        label = "Très robuste";
    }

    bar.style.width = width;
    bar.style.background = color;
    text.textContent = label + " – Le mot de passe doit contenir au moins 8 caractères, une lettre et un chiffre.";
});

document.getElementById('confirm_password').addEventListener('input', checkPasswordMatch);
document.getElementById('new_password').addEventListener('input', checkPasswordMatch);

function checkPasswordMatch() {
    const pwd = document.getElementById('new_password').value;
    const confirm = document.getElementById('confirm_password').value;
    const msg = document.getElementById('password-match-message');
    if (confirm && pwd !== confirm) {
        msg.textContent = "Les mots de passe ne correspondent pas.";
    } else {
        msg.textContent = "";
    }
}