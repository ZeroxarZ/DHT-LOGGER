    document.getElementById('copy-btn').onclick = function() {
        const code = document.getElementById('manual-code').innerText;
        navigator.clipboard.writeText(code);
        this.innerText = "Copié !";
        setTimeout(() => { this.innerText = "Copier"; }, 1500);
    };
    document.getElementById('enable-2fa-btn').onclick = function() {
        const secret = document.getElementById('secret').value;
        if (secret) {
            // Simulate enabling 2FA
            alert("2FA activé avec succès !");
            // Redirect or update UI as needed
        } else {
            alert("Veuillez entrer un secret valide.");
        }
    };