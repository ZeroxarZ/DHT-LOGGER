document.addEventListener("DOMContentLoaded", function() {
    // Gestion du clic sur le lien de renvoi
    const resendLink = document.getElementById("resend-link");
    if (resendLink) {
        resendLink.addEventListener("click", function(e) {
            e.preventDefault();
            resendLink.style.pointerEvents = "none";
            resendLink.style.color = "#888";
            resendLink.textContent = "Envoi...";
            document.getElementById("resendForm").submit();
        });
    }
});